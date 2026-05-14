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

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.schemas import (
    RacePredictionResponse,
    WinnerPredictionResponse,
    DNFProbabilityResponse,
    StandingsResponse,
    CircuitListResponse,
    SimulationRequest,
)
from engine.predictor import predict, PredictionRequest
from data.circuit_data import get_circuit, get_all_circuits
from data.season_2026 import DRIVER_STANDINGS_AFTER_R4, CONSTRUCTOR_STANDINGS_AFTER_R4
from data.driver_data import get_driver, get_all_drivers

router = APIRouter()


@router.get("/predict/{race_id}", response_model=RacePredictionResponse)
def get_race_prediction(
    race_id: str,
    rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    n_simulations: int = Query(5000, ge=100, le=50000)
):
    """Full race prediction with all probability outputs."""
    try:
        circuit = get_circuit(race_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Circuit '{race_id}' not found")
    
    try:
        result = predict(PredictionRequest(
            circuit_id=race_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
        ))
        return RacePredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/predict/{race_id}/winner", response_model=WinnerPredictionResponse)
def get_winner_prediction(
    race_id: str,
    rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    n_simulations: int = Query(5000, ge=100, le=50000)
):
    """Win probability only."""
    try:
        circuit = get_circuit(race_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Circuit '{race_id}' not found")
    
    try:
        result = predict(PredictionRequest(
            circuit_id=race_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
        ))
        
        winners = [{"driver": p["driver"], "win_pct": p["win_pct"]} for p in result["predictions"]]
        winners.sort(key=lambda x: x["win_pct"], reverse=True)
        
        return WinnerPredictionResponse(predictions=winners)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Winner prediction failed: {str(e)}")


@router.get("/predict/{race_id}/dnf", response_model=DNFProbabilityResponse)
def get_dnf_prediction(
    race_id: str,
    rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
    n_simulations: int = Query(5000, ge=100, le=50000)
):
    """DNF probability only."""
    try:
        circuit = get_circuit(race_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Circuit '{race_id}' not found")
    
    try:
        result = predict(PredictionRequest(
            circuit_id=race_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
        ))
        
        dnfs = [{"driver": p["driver"], "dnf_pct": p["dnf_pct"]} for p in result["predictions"]]
        dnfs.sort(key=lambda x: x["dnf_pct"], reverse=True)
        
        return DNFProbabilityResponse(predictions=dnfs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DNF prediction failed: {str(e)}")


@router.get("/standings", response_model=StandingsResponse)
def get_standings():
    """Current championship standings."""
    try:
        return StandingsResponse(
            drivers=DRIVER_STANDINGS_AFTER_R4,
            constructors=CONSTRUCTOR_STANDINGS_AFTER_R4
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve standings: {str(e)}")


@router.get("/circuits", response_model=CircuitListResponse)
def list_circuits():
    """List all available circuits."""
    try:
        circuits = get_all_circuits()
        circuit_list = [{"id": cid, "name": c["name"], "location": c["city"]} for cid, c in circuits.items()]
        return CircuitListResponse(circuits=circuit_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve circuits: {str(e)}")


@router.post("/simulate", response_model=RacePredictionResponse)
def custom_simulation(request: SimulationRequest):
    """Custom simulation with parameter overrides."""
    try:
        circuit = get_circuit(request.race_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Circuit '{request.race_id}' not found")
    
    try:
        result = predict(PredictionRequest(
            circuit_id=request.race_id,
            rain_probability=request.rain_probability,
            n_simulations=request.n_simulations or 5000,
        ))
        return RacePredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")