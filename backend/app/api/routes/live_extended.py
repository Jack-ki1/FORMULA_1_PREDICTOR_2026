"""Live extended — win prob curve + timeline + mid-race re-sim + SSE live graph."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio, json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1", tags=["live-extended"])

@router.get("/live-win-prob/{race_id}")
async def live_win_prob(race_id: str, weather: str="dry", laps: int = 58):
    from backend.app.services.live_extended import simulate_win_prob_curve
    return simulate_win_prob_curve(race_id, weather=weather, laps_total=int(laps))

@router.get("/timeline/{race_id}")
async def timeline(race_id: str):
    from backend.app.services.live_extended import probability_timeline
    return probability_timeline(race_id)

@router.post("/live/resim")
async def live_resim(payload: dict):
    from backend.app.services.live_extended import mid_race_resim
    return mid_race_resim(payload.get("race_id","au"), payload.get("session_key",""), payload.get("gaps"), payload.get("pit_events"), payload.get("sc_deployed",False))

@router.get("/live/{session_key}/win-prob-stream")
async def win_prob_stream(session_key: str, race_id: str = "au"):
    """SSE that re-sims win prob every 3s from live gaps — the wow feature."""
    from backend.app.services.live_extended import mid_race_resim
    async def gen():
        for i in range(60):
            # In prod, pull real gaps from OpenF1; here synthesize evolving gaps
            gaps = {code: (i*0.2 + (hash(code)%10)*0.3) for code in ["VER","HAM","LEC","NOR","RUS","PIA"]}
            snap = mid_race_resim(race_id, session_key, gaps=gaps, sc_deployed=(i==20))
            # Also include prob curve point
            yield f"data: {json.dumps(snap, default=str)}\n\n"
            await asyncio.sleep(3)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
