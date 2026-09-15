from fastapi import APIRouter
router = APIRouter(prefix="/api/v1", tags=["alternate"])

@router.post("/replay/branch-point")
async def branch_point(payload: dict):
    from backend.app.services.alternate import branch_point_replay
    return branch_point_replay(payload.get("race_id","au"), int(payload.get("freeze_lap",25)), payload.get("altered") or payload.get("scenario") or {})

@router.get("/championship/counterfactual")
async def counterfactual(remove_dnf: bool = True, remove_sc: bool = False):
    from backend.app.services.alternate import counterfactual_championship
    return counterfactual_championship(remove_dnf, remove_sc)

@router.post("/transfer/simulate")
async def transfer(payload: dict):
    from backend.app.services.alternate import transfer_simulator
    return transfer_simulator(payload.get("driver"), payload.get("target_team"))

@router.get("/transfer/options")
async def transfer_options():
    from backend.app.config.team_driver_lineup_2026 import TEAMS_2026, get_all_drivers
    return {"teams": [{"id": t["id"], "name": t["name"]} for t in TEAMS_2026], "drivers": [{"code": d["code"], "name": d["name"], "team": d["team_id"]} for d in get_all_drivers()]}
