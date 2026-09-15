from fastapi import APIRouter
router = APIRouter(prefix="/api/v1", tags=["community"])

@router.post("/leaderboard/submit")
async def lb_submit(payload: dict):
    from backend.app.services.community import submit_pick
    return submit_pick(payload.get("user","anon"), payload.get("race_id","au"), payload.get("picks", payload.get("podium",[])))

@router.get("/leaderboard")
async def lb_get(race_id: str = "au"):
    from backend.app.services.community import leaderboard
    return leaderboard(race_id)

@router.get("/market/{race_id}")
async def market_prices(race_id: str):
    from backend.app.services.community import market_prices as _m
    return _m(race_id)

@router.post("/market/{race_id}/trade")
async def market_trade(race_id: str, payload: dict):
    from backend.app.services.community import market_trade as _t
    return _t(payload.get("user","anon"), race_id, payload.get("driver"), float(payload.get("amount",1)))

@router.get("/streak")
async def streak():
    from backend.app.services.community import hot_streak
    return hot_streak()
