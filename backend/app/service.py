"""Domain logic shared by the API routes."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

import httpx
import numpy as np

from . import engine
from .config import CHOICES, runtime
from .provider import CIRCUITS, SEED, TEAMS, cache_get, cache_put, circuit_meta, reset_cache, snapshot

DRIVERS = {d["code"]: d for d in SEED["drivers"]}


def parse_utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def race_id(r: dict) -> str:
    return f"{r['round']}"


def with_status(r: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    start = parse_utc(r["start_utc"])
    status = "completed" if now > start + timedelta(hours=3) else "live" if now >= start else "upcoming"
    day = lambda iso: date.fromisoformat(iso).strftime("%A")
    d_end = date.fromisoformat(r["date_end"])
    labels = dict(practice_day=day(r["date_start"]), quali_day=(d_end - timedelta(days=1)).strftime("%A"), race_day=day(r["date_end"]))
    return {**r, "id": race_id(r), "status": status, "labels": labels, "sprint": r.get("sprint", False),
            "circuit": circuit_meta(r["circuit_id"], r.get("circuit_name", ""), r.get("locality", ""), r.get("lat"), r.get("lon"))}


async def calendar() -> list[dict]:
    snap = await snapshot()
    return [with_status(r) for r in snap["calendar"]]


async def find_race(rid: str | None) -> dict | None:
    cal = await calendar()
    if rid:
        return next((r for r in cal if r["id"] == rid), None)
    return next((r for r in cal if r["status"] != "completed"), cal[-1] if cal else None)


def team_info(tid: str) -> dict:
    t = TEAMS.get(tid)
    return dict(id=tid, name=t["name"], color=t["color"]) if t else dict(id=tid, name=tid.replace("_", " ").title(), color="#8d99b5")


async def build_field(snap: dict) -> list[dict]:
    rounds = max(1, snap["as_of_round"])
    codes = list(DRIVERS) + [c for c in snap["drivers"] if c not in DRIVERS]
    field = []
    for code in codes:
        base, st = DRIVERS.get(code, {}), snap["drivers"].get(code, {})
        team = st.get("team") or base.get("team") or "haas"
        t = TEAMS.get(team, {"pace": 55, "rel": 0.93})
        pts = st.get("points")
        field.append(dict(code=code, name=base.get("name") or st.get("name") or code, team=team, cc=base.get("cc", ""),
                          pace=t["pace"], rel=t["rel"], skill=base.get("skill", 70), wet=base.get("wet", 70),
                          form=(pts / rounds) if pts is not None else None))
    return field


async def resolve_weather(requested: str, race: dict) -> tuple[str, dict | None]:
    fc = await forecast(race)
    if requested != "auto":
        return requested, fc
    p = (fc or {}).get("race_day", {}).get("rain_prob")
    return ("wet" if p is not None and p >= 60 else "mixed" if p is not None and p >= 30 else "dry"), fc


def resolve_grid(body, race: dict, snap: dict, codes: list[str]):
    """Returns (locked slots per driver or None, source label)."""
    if body.session in ("practice", "qualifying"):
        return None, "simulated"
    fixed = [-1] * len(codes)
    if body.grid_mode == "manual":
        seen: set[str] = set()
        for i, c in enumerate(body.grid[: len(codes)]):
            c = c.strip().upper()
            if not c:
                continue
            if c not in codes:
                raise ValueError(f"Unknown driver {c}")
            if c in seen:
                raise ValueError(f"Driver {c} is in more than one grid slot")
            seen.add(c)
            fixed[codes.index(c)] = i
        return (tuple(fixed) if seen else None), ("manual" if seen else "simulated")
    live = (snap.get("quali_by_round") or {}).get(race["round"])
    if live:
        for c, pos in live.items():
            if c in codes and 1 <= pos <= len(codes):
                fixed[codes.index(c)] = pos - 1
        if any(f >= 0 for f in fixed) and len({f for f in fixed if f >= 0}) == sum(f >= 0 for f in fixed):
            return tuple(fixed), "live"
    return None, "simulated"


async def run_prediction(body) -> dict:
    snap = await snapshot()
    race = await find_race(body.race_id)
    if race is None:
        raise KeyError("race")
    weather, fc = await resolve_weather(body.weather, race)
    field = await build_field(snap)
    fixed, gsource = resolve_grid(body, race, snap, [f["code"] for f in field])
    enhanced = body.enhanced if body.enhanced is not None else runtime["model_type"] == "monte_carlo_form"
    circ = race["circuit"]
    p = engine.Params(sims=body.sims, weather=weather, session=body.session, mech=body.mechanical_failures, sc=body.safety_car,
                      enhanced=enhanced, chaos=body.chaos, seed=body.seed, grid_fixed=fixed, grid_weight=body.grid_weight,
                      wet_influence=body.wet_influence, reliability=body.reliability, strategy_aggr=body.strategy_aggr,
                      sc_weight=body.sc_weight, team_w=body.team_w, driver_w=body.driver_w, track_w=body.track_w,
                      weather_w=body.weather_w, deg_w=body.deg_w, form_k=body.form_k, ci=body.ci)
    t0 = datetime.now()
    res = await asyncio.to_thread(engine.predict, field, circ, p, snap["rounds_done"])
    ms = (datetime.now() - t0).total_seconds() * 1000
    info = {f["code"]: f for f in field}
    teams: dict[str, float] = {}
    for d in res["drivers"]:
        teams[d["team"]] = teams.get(d["team"], 0.0) + d["avg_points"]
        d["team"] = team_info(d["team"])
        d["cc"] = info[d["code"]]["cc"]
        d["number"] = (DRIVERS.get(d["code"]) or {}).get("number")
    team_points = sorted([dict(team=team_info(t), points=round(v, 2)) for t, v in teams.items()], key=lambda x: -x["points"])
    rain = ((fc or {}).get("race_day") or {}).get("rain_prob")
    echo = body.model_dump(exclude={"grid"})
    return dict(race=race, params={**echo, "weather": weather, "weather_requested": body.weather, "enhanced": enhanced},
                forecast=fc, rain_prob=rain, grid_source=gsource, grid_locked=0 if fixed is None else sum(f >= 0 for f in fixed),
                team_points=team_points, source=snap["source"], as_of_round=snap["as_of_round"], elapsed_ms=round(ms, 1), **res)


async def grid_options(rid: str | None) -> dict:
    snap = await snapshot()
    race = await find_race(rid)
    if race is None:
        raise KeyError("race")
    field = await build_field(snap)
    codes = [f["code"] for f in field]
    base = engine.base_ratings(field, True)
    by_form = [codes[i] for i in sorted(range(len(codes)), key=lambda i: -base[i])]
    live = (snap.get("quali_by_round") or {}).get(race["round"])
    live_grid = None
    if live:
        order = sorted((pos, c) for c, pos in live.items() if c in codes)
        live_grid = [c for _, c in order]
    return dict(race_id=race["id"], live=live_grid, by_form=by_form)


def get_config() -> dict:
    from .config import settings
    return {**runtime, "admin_enabled": bool(settings.admin_token), "choices": {k: sorted(v) for k, v in CHOICES.items()}, "persistent": False}


def set_config(patch: dict) -> dict:
    for k, v in patch.items():
        if v is None:
            continue
        if k in CHOICES and v not in CHOICES[k]:
            raise ValueError(f"Invalid {k}")
        if k in ("cache_ttl", "live_interval"):
            v = int(v)
            if not (0 <= v <= 86400):
                raise ValueError(f"{k} must be between 0 and 86400 seconds")
        runtime[k] = v
    reset_cache()
    return get_config()


WMO = [(0, "Clear sky", "sun"), (2, "Partly cloudy", "partly"), (3, "Overcast", "cloud"), (48, "Fog", "fog"), (57, "Drizzle", "rain"),
       (67, "Rain", "rain"), (77, "Snow", "snow"), (82, "Rain showers", "rain"), (86, "Snow showers", "snow"), (99, "Thunderstorm", "storm")]


def wmo(code: int) -> tuple[str, str]:
    for hi, label, kind in WMO:
        if code <= hi:
            return label, kind
    return "Unknown", "cloud"


async def forecast(race: dict) -> dict | None:
    key = f"wx:{race['id']}"
    if (hit := cache_get(key)) is not None:
        return hit or None
    c = race["circuit"]
    if c.get("lat") is None:
        return None
    try:
        async with httpx.AsyncClient(timeout=6) as cl:
            r = await cl.get("https://api.open-meteo.com/v1/forecast", params=dict(
                latitude=c["lat"], longitude=c["lon"], timezone="auto", start_date=race["date_start"], end_date=race["date_end"],
                daily="weather_code,temperature_2m_max,precipitation_probability_max,wind_speed_10m_max", hourly="relative_humidity_2m"))
            r.raise_for_status()
        j = r.json()
        d, hum = j["daily"], j["hourly"]["relative_humidity_2m"]
        days = []
        for i, day in enumerate(d["time"]):
            label, kind = wmo(int(d["weather_code"][i] or 0))
            h = [v for t, v in zip(j["hourly"]["time"], hum) if t.startswith(day) and v is not None]
            days.append(dict(date=day, temp=d["temperature_2m_max"][i], rain_prob=d["precipitation_probability_max"][i],
                             wind=d["wind_speed_10m_max"][i], humidity=round(sum(h) / len(h)) if h else None, label=label, kind=kind))
        return cache_put(key, dict(days=days, race_day=days[-1], units=dict(temp="°C", wind="km/h")), 1800)
    except Exception:
        cache_put(key, False, 300)
        return None


async def standings() -> dict:
    snap = await snapshot()
    f = {x["code"]: x for x in await build_field(snap)}
    drv = []
    for code, st in snap["drivers"].items():
        if st.get("points") is None:
            continue
        drv.append(dict(code=code, name=f[code]["name"] if code in f else st.get("name", code), team=team_info(st.get("team") or ""),
                        cc=f.get(code, {}).get("cc", ""), points=st["points"], wins=st.get("wins"), podiums=st.get("podiums")))
    drv.sort(key=lambda x: -x["points"])
    for i, x in enumerate(drv, 1):
        x["pos"] = i
    cons = snap.get("constructors")
    if cons:
        con = [dict(pos=c["pos"], team=team_info(c["id"]), points=c["points"], wins=c["wins"]) for c in cons]
    else:  # offline: sum only fully-known teams
        sums: dict[str, list] = {}
        for d in SEED["drivers"]:
            sums.setdefault(d["team"], []).append(d["points"])
        con = sorted([dict(team=team_info(t), points=sum(v), wins=None) for t, v in sums.items() if all(x is not None for x in v)], key=lambda x: -x["points"])
        for i, x in enumerate(con, 1):
            x["pos"] = i
    return dict(source=snap["source"], as_of_round=snap["as_of_round"], note=snap.get("note"), drivers=drv, constructors=con)


async def h2h(a: str, b: str, race_id_: str | None) -> dict:
    snap = await snapshot()
    from .routes_models import PredictIn  # local import avoids cycle
    pred = await run_prediction(PredictIn(race_id=race_id_, sims=4000))
    pd = {d["code"]: d for d in pred["drivers"]}
    if a not in pd or b not in pd:
        raise KeyError("driver")
    sa, sb = snap["drivers"].get(a, {}), snap["drivers"].get(b, {})
    fa, fb = sa.get("finishes"), sb.get("finishes")
    rec = None
    if fa and fb:
        common = set(fa) & set(fb)
        rec = [sum(fa[r] < fb[r] for r in common), sum(fb[r] < fa[r] for r in common)]
    side = lambda c, s: dict(code=c, name=pd[c]["name"], team=pd[c]["team"], cc=pd[c]["cc"], points=s.get("points"), wins=s.get("wins"),
                             podiums=s.get("podiums"), avg_quali=s.get("avg_grid"), win_prob=pd[c]["win"], podium_prob=pd[c]["podium"],
                             exp_pos=pd[c]["exp_pos"], pole_prob=pd[c]["pole"])
    return dict(race=pred["race"], a=side(a, sa), b=side(b, sb), record=rec, source=snap["source"])


async def recent() -> list[dict]:
    cal = await calendar()
    done = [r for r in cal if r["status"] == "completed"][-3:][::-1]
    nxt = next((r for r in cal if r["status"] != "completed"), None)
    out = [dict(id=r["id"], name=r["name"], cc=r["cc"], winner=r.get("winner"), winner_name=DRIVERS.get(r.get("winner") or "", {}).get("name"),
                points=25 if r.get("winner") else None, next=False) for r in done]
    if nxt:
        out.append(dict(id=nxt["id"], name=nxt["name"], cc=nxt["cc"], winner=None, winner_name=None, points=None, next=True))
    return out


async def fantasy_pool(rid: str | None, budget: float = 100.0, picks: int = 5) -> dict:
    from .routes_models import PredictIn
    pred = await run_prediction(PredictIn(race_id=rid, sims=4000))
    field = await build_field(await snapshot())
    base = engine.base_ratings(field, True)
    r01 = {f["code"]: float(np.clip((base[i] + 2) / 4, 0, 1)) for i, f in enumerate(field)}
    pool = [dict(code=d["code"], name=d["name"], team=d["team"], cc=d["cc"], price=round(6 + 24 * r01[d["code"]], 1),
                 exp_points=round(d["avg_points"], 2)) for d in pred["drivers"]]
    W = int(round(budget * 10))
    best = [[(0.0, ()) if k == 0 else (-1e9, ()) for _ in range(W + 1)] for k in range(picks + 1)]  # DP: exactly k picks, budget units
    for i, p in enumerate(pool):
        c = int(round(p["price"] * 10))
        for k in range(picks, 0, -1):
            for w in range(W, c - 1, -1):
                v = best[k - 1][w - c]
                if v[0] + p["exp_points"] > best[k][w][0]:
                    best[k][w] = (v[0] + p["exp_points"], v[1] + (i,))
    top = max(best[picks], key=lambda x: x[0])
    return dict(race=pred["race"], budget=budget, picks=picks, pool=pool, optimal=[pool[i]["code"] for i in top[1]], optimal_points=round(top[0], 2))


async def search(q: str) -> dict:
    q = q.strip().lower()
    if len(q) < 1:
        return dict(races=[], drivers=[], teams=[])
    cal = await calendar()
    snap = await snapshot()
    f = await build_field(snap)
    races = [dict(id=r["id"], name=r["name"], cc=r["cc"], circuit=r["circuit"]["name"]) for r in cal if q in (r["name"] + r["circuit"]["name"] + r["country"]).lower()][:5]
    drivers = [dict(code=d["code"], name=d["name"], team=team_info(d["team"]), cc=d["cc"]) for d in f if q in (d["name"] + d["code"]).lower()][:6]
    teams = [team_info(t["id"]) for t in SEED["teams"] if q in t["name"].lower() or q in t["full"].lower()][:4]
    return dict(races=races, drivers=drivers, teams=teams)
