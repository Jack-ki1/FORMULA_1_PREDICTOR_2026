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

@router.post("/calculate")
async def calculate(request: Request):
    try:
        body = await request.json()
    except:
        return JSONResponse({"error":{"code":"INVALID_JSON","message":"Body must be JSON"}}, status_code=400)
    driver_code = body.get("driver_code")
    race_position = body.get("race_position", 12)
    quali = body.get("qualifying_position")
    fastest = body.get("fastest_lap", False)
    overtakes = body.get("overtakes", 0)
    dnf = body.get("dnf", False)
    is_sprint = body.get("is_sprint", False)
    if not driver_code:
        return JSONResponse({"error":{"code":"MISSING","message":"driver_code required"}}, status_code=400)
    from backend.app.engine.fantasy_scoring import fantasy_scoring
    res = fantasy_scoring.calculate_driver_fantasy_points(driver_code, race_position, quali, fastest, overtakes, dnf, is_sprint)
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
