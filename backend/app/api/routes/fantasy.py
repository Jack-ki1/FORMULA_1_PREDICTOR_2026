from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time

router = APIRouter(prefix="/api/v1/fantasy", tags=["fantasy"])

# In-memory roster store (would be DB with auth in prod)
_rosters: Dict[str, Dict[str, Any]] = {}

@router.get("/scoring")
async def scoring_rules():
    from backend.app.engine.fantasy_scoring import fantasy_scoring
    return {"scoring": fantasy_scoring.scoring_rules, "note": "Real 2026 F1 Fantasy rules — replaces JSX approximation"}

# The game's *structural* constraints ($100M cap, 5+2 roster, transfer rules,
# $3M price floor, the 6 chips). Distinct from /scoring, which is point maths.
# The frontend previously guessed at these; this is the single source of truth.
# (modify.md section 5)
FANTASY_RULES_2026 = {
    "season": 2026,
    "game": "F1 Fantasy (fantasy.formula1.com)",
    "budget": {"salary_cap_millions": 100, "price_floor_millions": 3},
    "roster": {
        "drivers": 5,
        "constructors": 2,
        "total_assets": 7,
        "boost": {"count": 1, "multiplier": 2, "note": "one 2x boost driver per round"},
    },
    "transfers": {
        "free_per_round": 2,
        "max_carryover": 1,
        "max_available_per_round": 3,
        "extra_transfer_penalty_points": -10,
        "net_change_rule": (
            "a swap reversed within the same transfer window consumes zero "
            "transfers — transfers are calculated on NET change, not gross moves"
        ),
    },
    "price_changes": {
        "tier_a_threshold_millions": 18.5,
        "tier_a_step_millions": 0.3,
        "tier_b_step_millions": 0.6,
        "basis": "3-race points-per-million rolling average",
    },
    "chips": [
        {"id": "wildcard", "name": "Wildcard", "effect": "unlimited transfers, salary cap still applies", "uses": "once per season"},
        {"id": "limitless", "name": "Limitless", "effect": "no salary cap and unlimited transfers for one round", "uses": "once per season"},
        {"id": "extra_drs", "name": "Extra DRS", "effect": "3x boost on one driver, stacks with the 2x boost", "uses": "once per season"},
        {"id": "no_negative", "name": "No Negative", "effect": "negative scores are treated as zero", "uses": "once per season"},
        {"id": "autopilot", "name": "Autopilot", "effect": "highest-scoring driver is auto-captained", "uses": "once per season"},
        {"id": "final_fix", "name": "Final Fix", "effect": "change one driver after qualifying", "uses": "once per season"},
    ],
}

@router.get("/rules")
async def fantasy_rules():
    """The actual 2026 F1 Fantasy ruleset context (modify.md section 5)."""
    return FANTASY_RULES_2026

def _bad_request(code: str, message: str, details: dict | None = None):
    return JSONResponse(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status_code=400,
    )

# Accepted aliases so a reasonable-but-differently-named field doesn't silently
# produce a wrong answer. `finish_position` used to fall through to the default
# of 12 and return a plausible-looking all-zero score with HTTP 200 — a typo
# has to be loud, not quietly wrong (modify.md section 4).
_RACE_POSITION_ALIASES = ("race_position", "finish_position", "position", "race_pos")
_QUALI_POSITION_ALIASES = ("qualifying_position", "quali_position", "grid_position", "quali_pos")

@router.post("/calculate")
async def calculate(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _bad_request("INVALID_JSON", "Body must be JSON")
    if not isinstance(body, dict):
        return _bad_request("INVALID", "Body must be a JSON object")

    driver_code = body.get("driver_code") or body.get("code")
    if not driver_code:
        return _bad_request("MISSING", "driver_code required", {"accepted": ["driver_code", "code"]})
    driver_code = str(driver_code).upper()
    try:
        from backend.app.config.team_driver_lineup_2026 import get_driver_by_code
        if not get_driver_by_code(driver_code):
            return _bad_request("UNKNOWN_DRIVER", f"Unknown driver_code '{driver_code}'")
    except ImportError:
        pass
    race_position = None
    for key in _RACE_POSITION_ALIASES:
        if key in body:
            race_position = body[key]
            break
    if race_position is None:
        return _bad_request(
            "MISSING",
            "race_position required",
            {"accepted": list(_RACE_POSITION_ALIASES),
             "note": "no implicit default — a missing position must fail loudly"},
        )
    try:
        race_position = int(race_position)
    except (TypeError, ValueError):
        return _bad_request("INVALID", "race_position must be an integer")
    from backend.app.config.constants import grid_size
    if not (1 <= race_position <= grid_size()):
        return _bad_request("INVALID", f"race_position must be between 1 and {grid_size()}")

    quali = None
    for key in _QUALI_POSITION_ALIASES:
        if key in body:
            quali = body[key]
            break
    if quali is not None:
        try:
            quali = int(quali)
            if not (1 <= quali <= grid_size()):
                return _bad_request("INVALID", f"qualifying_position must be between 1 and {grid_size()}")
        except (TypeError, ValueError):
            return _bad_request("INVALID", "qualifying_position must be an integer")

    fastest = bool(body.get("fastest_lap", False))
    try:
        overtakes = int(body.get("overtakes", 0) or 0)
    except (TypeError, ValueError):
        return _bad_request("INVALID", "overtakes must be an integer")
    dnf = bool(body.get("dnf", False))
    is_sprint = bool(body.get("is_sprint", False))

    from backend.app.engine.fantasy_scoring import fantasy_scoring
    res = fantasy_scoring.calculate_driver_fantasy_points(
        driver_code, race_position, quali, fastest, overtakes, dnf, is_sprint
    )
    return res

@router.post("/expected")
async def expected(request: Request):
    try:
        body = await request.json()
    except:
        return JSONResponse({"error":{"code":"INVALID_JSON","message":"Body must be JSON"}}, status_code=400)
    driver_code = body.get("driver_code")
    pred_pos = body.get("predicted_position", 12)
    grid = body.get("grid_position")
    if not driver_code:
        return JSONResponse({"error":{"code":"MISSING","message":"driver_code required"}}, status_code=400)
    from backend.app.engine.fantasy_scoring import fantasy_scoring
    res = fantasy_scoring.calculate_expected_fantasy_points(driver_code, pred_pos, grid)
    return res

@router.get("/optimal")
async def optimal(budget: int = 100, race_id: str = "au"):
    # Use Monte Carlo predictions to suggest optimal 5+2
    try:
        from backend.app.engine.monte_carlo import MonteCarloSimulator
        from backend.app.config.team_driver_lineup_2026 import get_all_drivers
        from backend.app.engine.fantasy_scoring import fantasy_scoring
        sim = MonteCarloSimulator(num_simulations=1500)
        # Quick grid from strength
        grid = {d["code"]: i+1 for i,d in enumerate(sorted(get_all_drivers(), key=lambda x: x["strength"], reverse=True))}
        out = sim.simulate_race(race_id, grid, "dry", 0.3, 30, 1500, seed=42)
        # Build race_predictions for fantasy_scoring
        race_preds = {}
        for code, vals in out["results"]["probabilities"].items():
            # predicted position = avg_position, grid = grid pos
            race_preds[code] = {"position": vals["avg_position"], "grid": grid[code]}
        # Get optimal picks via fantasy_scoring
        optimal = fantasy_scoring.get_optimal_picks(race_preds, budget=budget)
        # Enhance with expected points per driver
        enhanced = []
        for code, vals in race_preds.items():
            exp = fantasy_scoring.calculate_expected_fantasy_points(code, vals["position"], vals["grid"])
            enhanced.append({"driver_code": code, "expected": exp["expected_points"], "confidence": exp["confidence"], "pred_pos": vals["position"]})
        enhanced.sort(key=lambda x: x["expected"], reverse=True)
        return {"race_id": race_id, "optimal": optimal, "ranked": enhanced[:10], "budget": budget}
    except Exception as e:
        return JSONResponse({"error":{"code":"FAILED","message":str(e)}}, status_code=500)

@router.post("/transfers")
async def transfers(request: Request):
    """Model the real net-transfer rule (modify.md section 5).

    2026 scores transfers on NET change: a swap that is reversed inside the same
    transfer window costs nothing. Gross-move counting (the naive approach)
    over-charges for exactly that case, so this computes the symmetric difference
    between the outgoing and incoming sets and nets out reversals.
    """
    try:
        body = await request.json()
    except Exception:
        return _bad_request("INVALID_JSON", "Body must be JSON")
    if not isinstance(body, dict):
        return _bad_request("INVALID", "Body must be a JSON object")

    old_drivers = body.get("current_drivers") or []
    new_drivers = body.get("new_drivers") or []
    old_teams = body.get("current_constructors") or []
    new_teams = body.get("new_constructors") or []

    for label, val in (("current_drivers", old_drivers), ("new_drivers", new_drivers),
                       ("current_constructors", old_teams), ("new_constructors", new_teams)):
        if not isinstance(val, list):
            return _bad_request("INVALID", f"{label} must be a list")
    if len(new_drivers) != 5:
        return _bad_request("INVALID", "new_drivers must contain exactly 5 drivers", {"got": len(new_drivers)})
    if len(new_teams) != 2:
        return _bad_request("INVALID", "new_constructors must contain exactly 2 constructors", {"got": len(new_teams)})

    # NET change = symmetric difference. A driver in both old and new is not a
    # transfer at all; a driver removed then re-added nets to zero.
    out_drivers = sorted(set(old_drivers) - set(new_drivers))
    in_drivers = sorted(set(new_drivers) - set(old_drivers))
    out_teams = sorted(set(old_teams) - set(new_teams))
    in_teams = sorted(set(new_teams) - set(old_teams))

    gross_moves = len(out_drivers) + len(in_teams)
    transfers_used = max(len(out_drivers), len(in_teams))

    rules = FANTASY_RULES_2026["transfers"]
    free = rules["free_per_round"]
    carryover = 0
    if isinstance(body.get("carryover"), int):
        carryover = max(0, min(int(body["carryover"]), rules["max_carryover"]))
    available = min(free + carryover, rules["max_available_per_round"])
    extra = max(0, transfers_used - available)
    penalty = extra * rules["extra_transfer_penalty_points"]

    return {
        "transfers_used": transfers_used,
        "gross_moves": gross_moves,
        "reversed_within_window": len(set(old_drivers) & set(new_drivers)),
        "free_transfers_available": available,
        "free_transfers_used": min(transfers_used, available),
        "extra_transfers": extra,
        "points_penalty": penalty,
        "out_drivers": out_drivers,
        "in_drivers": in_drivers,
        "out_constructors": out_teams,
        "in_constructors": in_teams,
        "carryover_next_round": 0 if extra > 0 else min(
            rules["max_carryover"], max(0, available - transfers_used)
        ),
        "rule": rules["net_change_rule"],
    }

@router.post("/roster")
async def save_roster(request: Request):
    try:
        body = await request.json()
    except:
        return JSONResponse({"error":{"code":"INVALID_JSON","message":"Body must be JSON"}}, status_code=400)
    user = body.get("user", "anon")
    drivers = body.get("drivers", [])
    constructors = body.get("constructors", [])
    if len(drivers)!=5 or len(constructors)!=2:
        return JSONResponse({"error":{"code":"INVALID","message":"Need 5 drivers and 2 constructors"}}, status_code=400)
    # Validate budget via simple price calc (would use real prices in prod)
    _rosters[user] = {"drivers": drivers, "constructors": constructors, "updated": time.time()}
    return {"ok": True, "user": user, "roster": _rosters[user]}

@router.get("/roster/{user}")
async def get_roster(user: str):
    return _rosters.get(user, {"drivers": [], "constructors": [], "note": "No roster yet"})

@router.get("/history/{driver_code}")
async def history(driver_code: str, last: int = 5):
    # Return last N race fantasy points for driver — uses season_2026_results as fallback
    try:
        from backend.app.data.season_2026 import get_all_race_results
        from backend.app.engine.fantasy_scoring import fantasy_scoring
        results = get_all_race_results()
        # Build per-race fantasy for driver
        hist = []
        for rnd, res in sorted(results.items()):
            # res has winner/podium, but not per-driver positions — synthesize
            # For demo, use winner/podium to infer positions
            pos = 1 if res["winner"]==driver_code else (2 if driver_code in res["podium"] else 12)
            quali = pos # proxy
            pts = fantasy_scoring.calculate_driver_fantasy_points(driver_code, pos, quali, False, 0, False, False)
            hist.append({"round": rnd, "position": pos, "fantasy": pts["total_points"]})
        return {"driver_code": driver_code, "history": hist[-last:]}
    except Exception as e:
        return JSONResponse({"error":{"code":"FAILED","message":str(e)}}, status_code=500)
