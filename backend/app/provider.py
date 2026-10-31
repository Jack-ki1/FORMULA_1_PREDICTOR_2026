"""Data layer: live Jolpica (Ergast-compatible) data with a bundled offline snapshot as fallback."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

from .config import runtime, settings

log = logging.getLogger("f1")
SEED = json.loads((Path(__file__).parent / "data" / "seed.json").read_text(encoding="utf-8"))
TEAMS = {t["id"]: t for t in SEED["teams"]}
CIRCUITS = SEED["circuits"]
ALIAS = {"rb": "racing_bulls", "alphatauri": "racing_bulls", "sauber": "audi", "kick_sauber": "audi", "alpine_f1_team": "alpine"}
CC = {"Australia": "AU", "China": "CN", "Japan": "JP", "Bahrain": "BH", "Saudi Arabia": "SA", "USA": "US", "United States": "US",
      "Canada": "CA", "Monaco": "MC", "Spain": "ES", "Austria": "AT", "UK": "GB", "United Kingdom": "GB", "Belgium": "BE",
      "Hungary": "HU", "Netherlands": "NL", "Italy": "IT", "Azerbaijan": "AZ", "Singapore": "SG", "Mexico": "MX", "Brazil": "BR",
      "Qatar": "QA", "UAE": "AE", "United Arab Emirates": "AE", "Malaysia": "MY", "Portugal": "PT", "Turkey": "TR"}
DEFAULT_CIRCUIT = dict(length_km=None, turns=None, lap_record=None, drs=None, laps=None, tyre_wear=0.5, overtaking=0.5, sc_prob=0.45)
CIRCUIT_ALIAS = {"madrid": "madring", "barcelona": "catalunya", "bahrain_in_malaysia": "sepang"}

_cache: dict[str, tuple[float, object]] = {}
_lock = asyncio.Lock()
_last_good: dict | None = None


def cache_get(k: str):
    v = _cache.get(k)
    return v[1] if v and v[0] > time.time() else None


def cache_put(k: str, val, ttl: float | None = None):
    _cache[k] = (time.time() + (ttl if ttl is not None else runtime["cache_ttl"]), val)
    return val


def reset_cache() -> None:
    _cache.clear()


def lap_seconds(s: str | None) -> float:
    try:
        m, sec = s.split(":")
        return int(m) * 60 + float(sec)
    except Exception:
        return 90.0


def circuit_meta(cid: str, name: str = "", locality: str = "", lat=None, lon=None) -> dict:
    cid = CIRCUIT_ALIAS.get(cid, cid)
    c = {**DEFAULT_CIRCUIT, "name": name or cid, "locality": locality, "lat": lat, "lon": lon, **CIRCUITS.get(cid, {})}
    c["id"] = cid
    c["lap_ref"] = lap_seconds(c.get("lap_record") or c.get("ref_lap"))
    return c


def estimate_sessions(start_utc: str, sprint: bool) -> list[dict]:
    """Typical session layout relative to lights-out. Used offline or when the live schedule has no session times."""
    r = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    h = lambda x: (r + timedelta(hours=x)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if sprint:
        items = [("FP1", "Practice 1", -53), ("SQ", "Sprint Qualifying", -49), ("SPR", "Sprint", -28), ("Q", "Qualifying", -24), ("R", "Grand Prix", 0)]
    else:
        items = [("FP1", "Practice 1", -50), ("FP2", "Practice 2", -46), ("FP3", "Practice 3", -27), ("Q", "Qualifying", -23), ("R", "Grand Prix", 0)]
    return [dict(key=k, name=n, start_utc=h(o), estimated=True) for k, n, o in items]


def team_id(raw: str) -> str:
    return ALIAS.get(raw, raw)


# ---------- parsers (pure, unit-tested) ----------
def parse_calendar(pages: list[dict], winners: dict[int, str]) -> list[dict]:
    out = []
    for m in pages:
        for r in m["RaceTable"]["Races"]:
            c, loc = r["Circuit"], r["Circuit"]["Location"]
            d_end = date.fromisoformat(r["date"])
            d_start = r.get("FirstPractice", {}).get("date") or (d_end - timedelta(days=2)).isoformat()
            rnd = int(r["round"])
            start = f"{r['date']}T{r.get('time', '14:00:00Z')}"
            sprint = "Sprint" in r
            keys = [("FirstPractice", "FP1", "Practice 1"), ("SecondPractice", "FP2", "Practice 2"), ("ThirdPractice", "FP3", "Practice 3"),
                    ("SprintQualifying", "SQ", "Sprint Qualifying"), ("SprintShootout", "SQ", "Sprint Qualifying"), ("Sprint", "SPR", "Sprint"), ("Qualifying", "Q", "Qualifying")]
            sess = [dict(key=k, name=nm, start_utc=f"{r[f]['date']}T{r[f].get('time', '12:00:00Z')}", estimated=False) for f, k, nm in keys if f in r]
            sess.append(dict(key="R", name="Grand Prix", start_utc=start, estimated=False))
            sess = sorted(sess, key=lambda x: x["start_utc"]) if len(sess) >= 4 else estimate_sessions(start, sprint)
            out.append(dict(round=rnd, circuit_id=c["circuitId"], name=r["raceName"], country=loc["country"], sprint=sprint, sessions=sess,
                            cc=CC.get(loc["country"], ""), date_start=d_start, date_end=r["date"],
                            start_utc=start, winner=winners.get(rnd),
                            circuit_name=c["circuitName"], locality=loc["locality"], lat=float(loc["lat"]), lon=float(loc["long"])))
    return sorted(out, key=lambda x: x["round"])


def parse_driver_standings(pages: list[dict]) -> tuple[int, dict]:
    lst = pages[0]["StandingsTable"]["StandingsLists"]
    if not lst:
        return 0, {}
    rows = {}
    for s in lst[0]["DriverStandings"]:
        d = s["Driver"]
        code = d.get("code") or d["familyName"][:3].upper()
        rows[code] = dict(points=float(s["points"]), wins=int(s["wins"]), pos=int(s["position"]),
                          team=team_id(s["Constructors"][-1]["constructorId"]) if s.get("Constructors") else None,
                          name=f"{d['givenName']} {d['familyName']}")
    return int(lst[0]["round"]), rows


def parse_constructors(pages: list[dict]) -> list[dict]:
    lst = pages[0]["StandingsTable"]["StandingsLists"]
    if not lst:
        return []
    return [dict(id=team_id(s["Constructor"]["constructorId"]), name=s["Constructor"]["name"], points=float(s["points"]),
                 wins=int(s["wins"]), pos=int(s["position"])) for s in lst[0]["ConstructorStandings"]]


def merge_races(pages: list[dict], key: str) -> dict[int, list]:
    out: dict[int, list] = {}
    for m in pages:
        for r in m["RaceTable"]["Races"]:
            out.setdefault(int(r["round"]), []).extend(r[key])
    return out


def parse_results(pages: list[dict]) -> tuple[dict, dict]:
    winners, finishes = {}, {}
    for rnd, rows in merge_races(pages, "Results").items():
        for x in rows:
            code, pos = x["Driver"].get("code"), int(x["position"])
            finishes.setdefault(code, {})[rnd] = pos
            if pos == 1:
                winners[rnd] = code
    return winners, finishes


def parse_quali(pages: list[dict]) -> tuple[dict[str, float], dict[int, dict[str, int]]]:
    grid: dict[str, list[int]] = {}
    by_round: dict[int, dict[str, int]] = {}
    for rnd, rows in merge_races(pages, "QualifyingResults").items():
        for x in rows:
            code, pos = x["Driver"].get("code"), int(x["position"])
            grid.setdefault(code, []).append(pos)
            by_round.setdefault(rnd, {})[code] = pos
    return {k: sum(v) / len(v) for k, v in grid.items()}, by_round


# ---------- snapshots ----------
def seed_snapshot() -> dict:
    cal = []
    for r in SEED["calendar"]:
        c = circuit_meta(r["circuit_id"])
        cal.append({**r, "circuit_name": c["name"], "locality": c["locality"], "lat": c["lat"], "lon": c["lon"], "sessions": estimate_sessions(r["start_utc"], r.get("sprint", False))})
    drivers = {d["code"]: dict(points=d["points"], wins=None, podiums=None, pos=None, avg_grid=None, finishes=None, team=d["team"])
               for d in SEED["drivers"]}
    ranked = sorted([c for c, v in drivers.items() if v["points"] is not None], key=lambda c: -drivers[c]["points"])
    for i, c in enumerate(ranked, 1):
        drivers[c]["pos"] = i
    return dict(source="seed", as_of_round=SEED["as_of_round"], rounds_done=SEED["as_of_round"], calendar=cal, drivers=drivers,
                constructors=None, quali_by_round={}, note=SEED["note"])


async def _pages(client: httpx.AsyncClient, path: str) -> list[dict]:
    out, offset = [], 0
    while True:
        r = await client.get(f"{settings.jolpica}{path}", params={"limit": 100, "offset": offset})
        r.raise_for_status()
        m = r.json()["MRData"]
        out.append(m)
        offset += 100
        await asyncio.sleep(0.3)  # stay under Jolpica's 4 req/s burst limit
        if offset >= int(m["total"]):
            return out


async def _live() -> dict:
    s = settings.season
    async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "f1-predictor-2026"}) as c:
        sched = await _pages(c, f"/{s}.json")
        dst = await _pages(c, f"/{s}/driverstandings.json")
        cst = await _pages(c, f"/{s}/constructorstandings.json")
        res = await _pages(c, f"/{s}/results.json")
        qua = await _pages(c, f"/{s}/qualifying.json")
    winners, finishes = parse_results(res)
    as_of, rows = parse_driver_standings(dst)
    grid, quali_by_round = parse_quali(qua)
    drivers = {}
    for code, v in rows.items():
        fin = finishes.get(code, {})
        drivers[code] = {**v, "podiums": sum(1 for p in fin.values() if p <= 3), "avg_grid": grid.get(code), "finishes": fin}
    return dict(source="live", as_of_round=as_of, rounds_done=max(winners) if winners else as_of,
                calendar=parse_calendar(sched, winners), drivers=drivers, constructors=parse_constructors(cst), quali_by_round=quali_by_round, note=None)


async def snapshot() -> dict:
    global _last_good
    if (hit := cache_get("snap")) is not None:
        return hit
    async with _lock:
        if (hit := cache_get("snap")) is not None:
            return hit
        if runtime["source_priority"] != "seed_only":
            try:
                _last_good = await asyncio.wait_for(_live(), 30)
                return cache_put("snap", _last_good)
            except Exception as e:  # network, rate limit, schema change -> degrade gracefully
                log.warning("live data unavailable (%s); using fallback", e)
                return cache_put("snap", _last_good or seed_snapshot(), 120)
        return cache_put("snap", seed_snapshot(), 600)
