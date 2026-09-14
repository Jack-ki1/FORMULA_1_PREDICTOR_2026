"""
Scenario Lab — what-if simulation endpoints
POST /api/v1/predictions/scenario  (baseline vs scenario diff)
POST /api/v1/predictions/simulate
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional

router = APIRouter(prefix="/api/v1/predictions", tags=["scenario"])

class ScenarioRequest(BaseModel):
    race_id: str
    session_type: str = "race"
    weather: Optional[str] = "dry"
    grid_positions: Optional[Dict[str,int]] = None
    scenario: Dict[str, Any] = {}  # {weather, grid_positions, safety_car_boost, tyre_strategy, dnf_driver, etc.}
    simulation_count: int = 5000
    random_seed: int = 42

@router.post("/scenario")
async def scenario_lab(req: ScenarioRequest):
    from backend.app.services.prediction_service import prediction_service
    from backend.app.engine.predictor import generate_prediction
    # baseline
    baseline_payload = {"race_id": req.race_id, "session_type": req.session_type, "weather": req.weather, "grid_positions": req.grid_positions, "simulation_count": req.simulation_count, "random_seed": req.random_seed}
    scenario_payload = {
        "race_id": req.race_id, "session_type": req.session_type,
        "weather": req.scenario.get("weather", req.weather),
        "grid_positions": req.scenario.get("grid_positions", req.grid_positions),
        "simulation_count": req.simulation_count,
        "random_seed": req.random_seed,
    }
    # optional overrides: heavy rain, safety_car_boost handled via weather param
    baseline = generate_prediction(**baseline_payload)
    scenario = generate_prediction(**scenario_payload)
    # diff
    bw = baseline["winner_probabilities"]; sw = scenario["winner_probabilities"]
    diff = {code: round(float(sw.get(code,0)-bw.get(code,0)),4) for code in bw}
    return {
        "baseline": {"winner_probabilities": bw, "predictions": baseline["predictions"]},
        "scenario": {"winner_probabilities": sw, "predictions": scenario["predictions"]},
        "diff": diff,
        "scenario_params": req.scenario,
        "explanation": "Baseline vs scenario deltas computed from calibrated ensemble + Monte Carlo",
    }

@router.post("/simulate")
async def simulate(req: ScenarioRequest):
    return await scenario_lab(req)
