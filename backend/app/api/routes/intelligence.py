from fastapi import APIRouter
router = APIRouter(prefix="/api/v1", tags=["intelligence"])

@router.get("/personas")
async def personas():
    from backend.app.services.intelligence import list_personas
    return {"personas": list_personas()}

@router.post("/personas/{team_id}/chat")
async def persona_chat(team_id: str, payload: dict):
    from backend.app.services.intelligence import persona_chat as _chat
    return _chat(team_id, payload.get("message",""), payload.get("race_id"))

@router.get("/preview/{race_id}")
async def preview(race_id: str):
    from backend.app.services.intelligence import auto_preview
    return auto_preview(race_id)

@router.get("/fingerprint")
async def fingerprint():
    from backend.app.services.intelligence import fingerprint_drivers
    return fingerprint_drivers()

@router.get("/meta/{race_id}")
async def meta(race_id: str):
    from backend.app.services.intelligence import meta_confidence
    return meta_confidence(race_id)

@router.post("/crowd/{race_id}/submit")
async def crowd_submit(race_id: str, payload: dict):
    from backend.app.services.intelligence import submit_crowd_podium
    return submit_crowd_podium(race_id, payload.get("picks", payload.get("podium", [])))

@router.get("/crowd/{race_id}")
async def crowd_vs_model(race_id: str):
    from backend.app.services.intelligence import model_vs_crowd
    return model_vs_crowd(race_id)
