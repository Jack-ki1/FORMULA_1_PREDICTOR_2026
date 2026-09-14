"""
Live Race — SSE + polling endpoints
GET /api/v1/live/{session_key}
GET /api/v1/live/{session_key}/stream  (SSE)
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio, json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/live", tags=["live"])

@router.get("/{session_key}")
async def live_snapshot(session_key: str):
    # federated providers: openf1 live where available, else fallback with clear mode
    mode = "historical_snapshot"
    data: dict = {}
    provenance = {}
    try:
        from backend.app.data.providers.registry import registry
        pit, pprov = await registry.get_pit_stops_federated(session_key)
        rc, rprov = await registry.get_race_control_federated(session_key)
        data["pit_stops"] = pit[:20] if isinstance(pit, list) else []
        data["race_control"] = rc[:20] if isinstance(rc, list) else []
        provenance["pit"] = pprov.to_dict() if hasattr(pprov, 'to_dict') else {}
        provenance["race_control"] = rprov.to_dict() if hasattr(rprov, 'to_dict') else {}
        # if openf1 returned data, it's live (subject to subscription)
        if pprov.provider == "openf1" or rprov.provider == "openf1":
            mode = "live"
        elif pprov.cache_status == "fallback":
            mode = "historical_snapshot"
    except Exception as e:
        data["error"] = str(e)
    return {
        "session_key": session_key,
        "mode": mode,
        "note": "live requires OpenF1 subscription; historical_snapshot uses last available data" if mode != "live" else "live telemetry via OpenF1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
        "provenance": provenance,
        "disclaimer": "Using latest historical snapshot — not pretending to be live" if mode=="historical_snapshot" else "",
    }

@router.get("/{session_key}/stream")
async def live_stream(session_key: str):
    async def gen():
        for i in range(60):  # 60 events then close; client reconnects
            snap = await live_snapshot(session_key)
            yield f"data: {json.dumps(snap, default=str)}\n\n"
            await asyncio.sleep(3)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
