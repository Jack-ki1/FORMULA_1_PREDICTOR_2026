from fastapi import APIRouter
router = APIRouter(prefix="/api/v1", tags=["sensory"])

@router.get("/sonify/{race_id}")
async def sonify(race_id: str, duration: int = 30):
    from backend.app.services.sensory import sonify_race
    return sonify_race(race_id, int(duration))

@router.get("/rivalry/graph")
async def rivalry():
    from backend.app.services.sensory import rivalry_graph
    return rivalry_graph()
