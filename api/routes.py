"""
FastAPI Routes for F1 Prediction API.

Endpoints:
  - /predict/{race_id}            → Full race prediction
  - /predict/{race_id}/winner     → Win probabilities only
  - /predict/{race_id}/dnf        → DNF risk per driver
  - /standings                    → Championship standings
  - /circuits                     → Circuit guide
  - /simulate                     → Custom simulation
"""
"""
NEWLY ADDED FIELDS :
FastAPI Route Handlers.

FIXES vs v1:
  - Import correct schema names (was causing startup ImportError)
  - get_all_circuits() returns a list, not dict — fixed .items() call
  - Response mapping aligned with actual predict() output structure
  - Added /health and proper error messages
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.schemas import (
    RacePredictionResponse, RaceMetaOut, DriverPredictionOut,
    WinnerPredictionResponse, DNFProbabilityResponse,
    StandingsResponse, StandingsEntry, ConstructorStandingsEntry,
    CircuitListResponse, CircuitSummary, CircuitResponse,
    SimulationRequest,
)
from engine.predictor import predict, PredictionRequest
from data.circuit_data import get_circuit, get_all_circuits
from data.season_2026 import DRIVER_STANDINGS_AFTER_R4, CONSTRUCTOR_STANDINGS_AFTER_R4
from data.driver_data import get_driver, get_all_drivers

router = APIRouter()


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "system": "F1 Prediction Engine 2026", "version": "2.0"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _result_to_response(result: dict) -> RacePredictionResponse:
    """Map predict() output dict → Pydantic response model."""
    meta = result["meta"]
    return RacePredictionResponse(
        meta=RaceMetaOut(**meta),
        predictions=[DriverPredictionOut(**p) for p in result["predictions"]],
        podium_predictions=result["podium_predictions"],
        likely_top_surprises=result["likely_top_surprises"],
    )


# ── Predictions ────────────────────────────────────────────────────────────────

@router.get("/predict/{circuit_id}", response_model=RacePredictionResponse, tags=["Predictions"])
async def predict_race(
    circuit_id: str,
    rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    n_simulations: int = Query(5000, ge=100, le=50000),
    seed: Optional[int] = Query(None, description="Seed for reproducible results"),
):
    """Full race outcome prediction for a given circuit."""
    try:
        get_circuit(circuit_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{circuit_id}' not found. "
                            f"Check GET /circuits for available IDs.")
    try:
        result = predict(PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            seed=seed,
        ))
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@router.get("/predict/{circuit_id}/winner", response_model=WinnerPredictionResponse, tags=["Predictions"])
async def predict_winner(
    circuit_id: str,
    rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    n_simulations: int = Query(2000, ge=100, le=20000),
):
    """Win probabilities only (fast response)."""
    try:
        get_circuit(circuit_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{circuit_id}' not found.")
    try:
        result = predict(PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            output_format="summary",
        ))
        top5 = sorted(result["predictions"], key=lambda x: x["win_pct"], reverse=True)[:5]
        return WinnerPredictionResponse(
            circuit=circuit_id,
            top_5_win_probabilities=[{"driver": p["driver"], "team": p["team"],
                                      "win_pct": p["win_pct"]} for p in top5],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{circuit_id}/dnf", response_model=DNFProbabilityResponse, tags=["Predictions"])
async def predict_dnf(
    circuit_id: str,
    n_simulations: int = Query(1000, ge=100, le=10000),
):
    """DNF risk per driver for this circuit."""
    try:
        get_circuit(circuit_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{circuit_id}' not found.")
    try:
        result = predict(PredictionRequest(circuit_id=circuit_id, n_simulations=n_simulations,
                                           output_format="summary"))
        dnf_list = sorted(result["predictions"], key=lambda x: x["dnf_pct"], reverse=True)
        return DNFProbabilityResponse(
            circuit=circuit_id,
            dnf_risk=[{"driver": p["driver"], "team": p["team"], "dnf_pct": p["dnf_pct"]}
                      for p in dnf_list],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate", response_model=RacePredictionResponse, tags=["Predictions"])
async def custom_simulation(request: SimulationRequest):
    """Custom simulation — supports rain, seed, and grid position overrides."""
    try:
        get_circuit(request.race_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{request.race_id}' not found.")
    try:
        result = predict(PredictionRequest(
            circuit_id=request.race_id,
            rain_probability=request.rain_probability,
            n_simulations=request.n_simulations or 5000,
            seed=request.seed,
            grid_overrides=request.grid_overrides or {},
        ))
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Standings ──────────────────────────────────────────────────────────────────

@router.get("/standings/drivers", tags=["Standings"])
async def driver_standings():
    """Current 2026 F1 Driver Championship standings."""
    result = []
    for s in DRIVER_STANDINGS_AFTER_R4:
        try:
            d = get_driver(s["driver"])
            name = d["name"]
        except KeyError:
            name = s["driver"]
        result.append(StandingsEntry(position=s["position"], driver=name, points=s["points"]))
    return result


@router.get("/standings/constructors", tags=["Standings"])
async def constructor_standings():
    return [ConstructorStandingsEntry(**s) for s in CONSTRUCTOR_STANDINGS_AFTER_R4]


@router.get("/standings", response_model=StandingsResponse, tags=["Standings"])
async def all_standings():
    """Combined driver + constructor standings."""
    drivers = []
    for s in DRIVER_STANDINGS_AFTER_R4:
        try:
            name = get_driver(s["driver"])["name"]
        except KeyError:
            name = s["driver"]
        drivers.append(StandingsEntry(position=s["position"], driver=name, points=s["points"]))
    constructors = [ConstructorStandingsEntry(**s) for s in CONSTRUCTOR_STANDINGS_AFTER_R4]
    return StandingsResponse(drivers=drivers, constructors=constructors)


# ── Circuits ───────────────────────────────────────────────────────────────────

@router.get("/circuits", response_model=CircuitListResponse, tags=["Circuits"])
async def list_circuits():
    """List all circuits in the 2026 calendar."""
    # FIX: get_all_circuits() returns a list, not a dict — v1 called .items() which crashed
    circuits = get_all_circuits()
    summaries = []
    for c in circuits:
        summaries.append(CircuitSummary(
            id=c["id"],
            name=c["name"],
            city=c["city"],
            country=c["country"],
            circuit_type=c.get("circuit_type", []),
            safety_car_probability=c.get("safety_car_probability", 0.5),
            overtaking_difficulty=c.get("overtaking_difficulty", 5),
            power_unit_demand=c.get("power_unit_demand", 5.0),
            brake_demand=c.get("brake_demand", 5.0),
            sprint_weekend=c.get("sprint_weekend", False),
            race_date=c.get("race_date", "TBC"),
        ))
    return CircuitListResponse(circuits=summaries)


@router.get("/circuits/{circuit_id}", tags=["Circuits"])
async def get_circuit_detail(circuit_id: str):
    """Full circuit profile."""
    try:
        return get_circuit(circuit_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{circuit_id}' not found.")


# ── Drivers ────────────────────────────────────────────────────────────────────

@router.get("/drivers", tags=["Drivers"])
async def list_drivers():
    return [
        {"id": d["id"], "name": d["name"], "team": d["team"],
         "nationality": d["nationality"], "number": d["number"],
         "championship_points": d["championship_points_2026"],
         "wins_2026": d["wins_2026"], "elo": d["elo"]}
        for d in get_all_drivers()
    ]


@router.get("/drivers/{driver_id}", tags=["Drivers"])
async def get_driver_detail(driver_id: str):
    try:
        return get_driver(driver_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Driver '{driver_id}' not found.")