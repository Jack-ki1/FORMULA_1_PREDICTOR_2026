import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from api.schemas import PredictionResponse, PredictionRequest as ApiPredictionRequest

# Backwards-compatible aliases for older route module imports.
RacePredictionResponse = PredictionResponse

# Lightweight response/request models for endpoints that only need a small shape.
# These are imported lazily by FastAPI at runtime, but we define minimal BaseModels here
# to keep routes importable even if the schema module is out of sync.
from pydantic import BaseModel

class WinnerPredictionResponse(BaseModel):
    predictions: list

class DNFProbabilityResponse(BaseModel):
    predictions: list

class StandingsResponse(BaseModel):
    drivers: list
    constructors: list

class CircuitListResponse(BaseModel):
    circuits: list

class SimulationRequest(BaseModel):
    race_id: str
    rain_probability: Optional[float] = None
    n_simulations: Optional[int] = None
    seed: Optional[int] = None
    output_format: str = "full"
    bypass_cache: bool = False
    use_stale: bool = False

from engine.predictor import predict, PredictionRequest

from data.circuit_data import get_circuit, get_all_circuits, CIRCUITS
from data.season_2026 import DRIVER_STANDINGS_AFTER_R4, CONSTRUCTOR_STANDINGS_AFTER_R4
from config.settings import API_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple in-memory cache for predictions
prediction_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = API_CONFIG.cache_ttl_seconds  # seconds


def _generate_cache_key(params: Dict[str, Any]) -> str:
    """Generate a unique cache key from prediction parameters."""
    # Sort params to ensure consistent key generation regardless of parameter order
    sorted_params = json.dumps(params, sort_keys=True)
    return hashlib.md5(sorted_params.encode()).hexdigest()


def _is_cache_valid(timestamp: datetime) -> bool:
    """Check if cached result is still valid."""
    return datetime.now() - timestamp < timedelta(seconds=CACHE_TTL)


@router.get("/predict/{race_id}", response_model=RacePredictionResponse)
def get_race_prediction(race_id: str,
                        rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
                        n_simulations: int = Query(5000, ge=100, le=50000)):
    """Full race prediction with all probability outputs."""
    try:
        # Validate circuit exists
        circuit = get_circuit(race_id)
        
        # Validate simulation count
        min_sim, max_sim = API_CONFIG.simulation_count_bounds
        n_simulations = max(min_sim, min(n_simulations, max_sim))
        
        # Generate cache key
        cache_params = {
            'circuit_id': race_id,
            'rain_probability': rain_probability,
            'n_simulations': n_simulations,
            'seed': None
        }
        cache_key = _generate_cache_key(cache_params)
        
        # Check cache if enabled
        if API_CONFIG.cache_enabled:
            if cache_key in prediction_cache:
                cached_result, timestamp = prediction_cache[cache_key]
                if _is_cache_valid(timestamp):
                    logger.info(f"Cache hit for {race_id}")
                    return cached_result
                else:
                    # Remove expired cache entry
                    del prediction_cache[cache_key]
        
        # Create prediction request object
        pred_request = PredictionRequest(
            circuit_id=race_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations
        )
        
        # Perform prediction
        logger.info(f"Generating prediction for circuit: {race_id}")
        result = predict(pred_request)
        
        # Cache result if caching is enabled
        if API_CONFIG.cache_enabled:
            prediction_cache[cache_key] = (result, datetime.now())
            
        return result
        
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{race_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
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
    """List all available circuits with full details."""
    try:
        circuits = get_all_circuits()
        circuit_list = []
        for circuit_id, circuit in circuits.items():
            circuit_list.append({
                "id": circuit_id,
                "name": circuit.name,
                "location": f"{circuit.city}, {circuit.country}",
                "date": circuit.race_date,
                "sprint_weekend": circuit.sprint_weekend
            })
        
        # Sort by race date
        circuit_list.sort(key=lambda x: x["date"])
        return CircuitListResponse(circuits=circuit_list)
    except Exception as e:
        logger.error(f"Error retrieving circuits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve circuits: {str(e)}")


class CacheControl(BaseModel):
    bypass_cache: bool = False
    use_stale: bool = False

@router.post("/simulate", response_model=RacePredictionResponse)
def custom_simulation(request: SimulationRequest):
    """Custom simulation with parameter overrides and caching options."""
    try:
        # Validate circuit exists
        circuit = get_circuit(request.race_id)
        
        # Validate simulation count
        min_sim, max_sim = API_CONFIG.simulation_count_bounds
        n_simulations = request.n_simulations or 5000
        n_simulations = max(min_sim, min(n_simulations, max_sim))
        
        # Validate rain probability
        rain_probability = request.rain_probability
        if rain_probability is not None:
            rain_probability = max(0.0, min(1.0, rain_probability))
        
        # Generate cache key
        cache_params = {
            'circuit_id': request.race_id,
            'rain_probability': rain_probability,
            'n_simulations': n_simulations,
            'seed': request.seed
        }
        cache_key = _generate_cache_key(cache_params)
        
        # Check cache if enabled and not bypassed
        if API_CONFIG.cache_enabled and not request.bypass_cache:
            if cache_key in prediction_cache:
                cached_result, timestamp = prediction_cache[cache_key]
                if _is_cache_valid(timestamp):
                    logger.info(f"Cache hit for {request.race_id}")
                    return cached_result
                elif request.use_stale:
                    logger.info(f"Using stale cache for {request.race_id}")
                    return cached_result
                else:
                    # Remove expired cache entry
                    del prediction_cache[cache_key]
        
        # Create prediction request object
        pred_request = PredictionRequest(
            circuit_id=request.race_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            seed=request.seed,
            output_format=request.output_format
        )
        
        # Perform prediction
        logger.info(f"Generating prediction for circuit: {request.race_id}")
        result = predict(pred_request)
        
        # Cache result if caching is enabled and not bypassed
        if API_CONFIG.cache_enabled and not request.bypass_cache:
            prediction_cache[cache_key] = (result, datetime.now())
            
        return result
        
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{request.race_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")