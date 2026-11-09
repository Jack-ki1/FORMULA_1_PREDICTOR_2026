import hmac

from fastapi import APIRouter, Header, HTTPException, Query, Response

from . import service
from .provider import snapshot
from .config import settings
from .routes_models import ConfigPatch, FantasyEvaluateIn, H2HIn, PredictIn

router = APIRouter(prefix="/api/v1")


def cached(resp: Response, s: int = 300, swr: int = 600):
    resp.headers["Cache-Control"] = f"public, s-maxage={s}, stale-while-revalidate={swr}"


@router.get("/meta")
async def meta(resp: Response):
    cached(resp, 60)
    s = await snapshot()
    return dict(season=2026, source=s["source"], as_of_round=s["as_of_round"], rounds_done=s["rounds_done"], note=s.get("note"),
                max_sims=settings.max_sims)


@router.get("/races")
async def races(resp: Response):
    cached(resp, 300)
    return await service.calendar()


@router.get("/races/next")
async def next_race(resp: Response):
    cached(resp, 60)
    r = await service.find_race(None)
    if not r:
        raise HTTPException(404, "No races available")
    return r


@router.get("/races/{rid}/weather")
async def weather(rid: str, resp: Response):
    cached(resp, 900)
    r = await service.find_race(rid)
    if not r:
        raise HTTPException(404, "Unknown race")
    return dict(forecast=await service.forecast(r))


@router.get("/drivers")
async def drivers(resp: Response):
    cached(resp, 600)
    f = await service.build_field(await snapshot())
    return [dict(code=d["code"], name=d["name"], team=service.team_info(d["team"]), cc=d["cc"]) for d in f]


@router.get("/standings")
async def standings(resp: Response):
    cached(resp, 300)
    return await service.standings()


@router.post("/predictions")
async def predictions(body: PredictIn):
    try:
        return await service.run_prediction(body)
    except KeyError:
        raise HTTPException(404, "Unknown race")
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/h2h")
async def h2h(a: str, b: str, resp: Response, race_id: str | None = None):
    cached(resp, 120)
    if a == b:
        raise HTTPException(422, "Pick two different drivers")
    try:
        return await service.h2h(a.upper(), b.upper(), race_id)
    except KeyError:
        raise HTTPException(404, "Unknown driver or race")


@router.post("/h2h")
async def h2h_post(body: H2HIn):
    """Head-to-head with user params (POST). GET /h2h remains as a deprecated thin wrapper."""
    if body.a == body.b:
        raise HTTPException(422, "Pick two different drivers")
    try:
        return await service.h2h(body.a.upper(), body.b.upper(), body.race_id, body)
    except KeyError:
        raise HTTPException(404, "Unknown driver or race")


@router.get("/recent")
async def recent(resp: Response):
    cached(resp, 300)
    return await service.recent()


@router.get("/fantasy/pool")
async def fantasy(resp: Response, race_id: str | None = None):
    cached(resp, 300)
    try:
        return await service.fantasy_pool(race_id)
    except KeyError:
        raise HTTPException(404, "Unknown race")


@router.post("/fantasy/evaluate")
async def fantasy_evaluate(body: FantasyEvaluateIn):
    """Full fantasy evaluation with user params (POST). GET /fantasy/pool remains as a deprecated wrapper."""
    try:
        return await service.fantasy_evaluate(body)
    except KeyError:
        raise HTTPException(404, "Unknown race")


@router.get("/search")
async def search(resp: Response, q: str = Query("", max_length=40)):
    cached(resp, 300)
    return await service.search(q)


@router.get("/races/{rid}/grid")
async def grid(rid: str, resp: Response):
    cached(resp, 60)
    try:
        return await service.grid_options(rid)
    except KeyError:
        raise HTTPException(404, "Unknown race")


@router.get("/config")
async def config(resp: Response):
    cached(resp, 30)
    return service.get_config()


def _admin(token: str | None):
    if not settings.admin_token:
        raise HTTPException(403, "SETTINGS_ADMIN_TOKEN is not configured on the server, so admin changes are disabled.")
    if not token or not hmac.compare_digest(token, settings.admin_token):
        raise HTTPException(401, "Invalid admin token")


@router.get("/admin/verify")
async def admin_verify(x_admin_token: str | None = Header(None)):
    _admin(x_admin_token)
    return {"ok": True}


@router.put("/admin/config")
async def admin_config(patch: ConfigPatch, x_admin_token: str | None = Header(None)):
    _admin(x_admin_token)
    try:
        return service.set_config(patch.model_dump())
    except ValueError as e:
        raise HTTPException(422, str(e))
