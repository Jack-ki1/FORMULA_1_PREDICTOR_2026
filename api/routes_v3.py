"""
API Routes v3.0 — Enhanced with H2H, constructor predictions, and live data.

New endpoints:
- /h2h: Head-to-head driver comparison
- /constructors: Constructor championship predictions
- /accuracy: Prediction accuracy tracking
- /live: Live race predictions (future)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict
from pydantic import BaseModel
import logging

from api.schemas import PredictionRequest, PredictionResponse
from engine.predictor import predict as run_predict
from engine.probability_model import predict_race
from database.models import get_db, Prediction as PredictionModel, Driver as DriverModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Existing Predict Endpoint ─────────────────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Run a race outcome prediction."""
    try:
        result = run_predict(request)
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Circuit not found: {e}")
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── NEW: Head-to-Head Comparison ──────────────────────────────────────────────

class H2HRequest(BaseModel):
    driver1: str
    driver2: str
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 10000


class H2HResponse(BaseModel):
    driver1: str
    driver2: str
    driver1_finishes_ahead_pct: float
    driver2_finishes_ahead_pct: float
    driver1_avg_position: float
    driver2_avg_position: float
    historical_h2h_wins: Optional[int]
    notes: str


@router.post("/h2h", response_model=H2HResponse)
async def head_to_head(request: H2HRequest):
    """
    Head-to-head driver comparison.
    
    Compares two drivers and calculates:
    - Probability driver1 finishes ahead of driver2
    - Expected position gap
    - Historical head-to-head record
    """
    try:
        # Run race simulation
        sim_result = predict_race(
            circuit_id=request.circuit_id,
            rain_probability=request.rain_probability,
            n_simulations=request.n_simulations,
        )
        
        # Extract driver predictions
        predictions = {p["driver_id"]: p for p in sim_result["predictions"]}
        
        if request.driver1 not in predictions:
            raise HTTPException(status_code=404, detail=f"Driver {request.driver1} not found")
        if request.driver2 not in predictions:
            raise HTTPException(status_code=404, detail=f"Driver {request.driver2} not found")
        
        driver1_pred = predictions[request.driver1]
        driver2_pred = predictions[request.driver2]
        
        # Calculate probability driver1 finishes ahead
        # Approximation: use position distributions
        pos_dist_1 = driver1_pred.get("position_distribution", [])
        pos_dist_2 = driver2_pred.get("position_distribution", [])
        
        p_driver1_ahead = 0.0
        for pos1 in range(len(pos_dist_1)):
            for pos2 in range(len(pos_dist_2)):
                if pos1 < pos2:  # Lower position number = better finish
                    p_driver1_ahead += pos_dist_1[pos1] * pos_dist_2[pos2]
        
        # Normalize
        total = p_driver1_ahead + (1 - p_driver1_ahead)
        p_driver1_ahead = p_driver1_ahead / total if total > 0 else 0.5
        
        return H2HResponse(
            driver1=driver1_pred["driver_name"],
            driver2=driver2_pred["driver_name"],
            driver1_finishes_ahead_pct=round(p_driver1_ahead * 100, 2),
            driver2_finishes_ahead_pct=round((1 - p_driver1_ahead) * 100, 2),
            driver1_avg_position=driver1_pred["expected_position_float"],
            driver2_avg_position=driver2_pred["expected_position_float"],
            historical_h2h_wins=None,  # TODO: Fetch from database
            notes=f"Based on {request.n_simulations:,} Monte Carlo simulations",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"H2H comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── NEW: Constructor Predictions ──────────────────────────────────────────────

class ConstructorPrediction(BaseModel):
    constructor: str
    predicted_points: float
    predicted_positions: List[int]
    points_ci_lower: float
    points_ci_upper: float


@router.get("/constructors/{circuit_id}")
async def predict_constructors(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = 10000,
):
    """
    Constructor (team) championship predictions.
    
    Returns predicted points for each constructor based on both drivers' results.
    """
    try:
        # Get driver predictions
        sim_result = predict_race(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
        )
        
        # Aggregate by constructor
        constructor_predictions = {}
        
        for driver_pred in sim_result["predictions"]:
            team = driver_pred["team"]
            
            if team not in constructor_predictions:
                constructor_predictions[team] = {
                    "drivers": [],
                    "total_points": 0.0,
                }
            
            # Calculate points based on predicted position
            pos = driver_pred["predicted_position"]
            points = _get_points_for_position(pos)
            
            constructor_predictions[team]["drivers"].append({
                "driver": driver_pred["driver_name"],
                "position": pos,
                "points": points,
            })
            constructor_predictions[team]["total_points"] += points
        
        # Build response
        results = []
        for team, data in constructor_predictions.items():
            results.append({
                "constructor": team.replace("_", " ").title(),
                "predicted_points": round(data["total_points"], 1),
                "driver_positions": [d["position"] for d in data["drivers"]],
            })
        
        # Sort by points
        results.sort(key=lambda x: x["predicted_points"], reverse=True)
        
        return {"constructors": results}
        
    except Exception as e:
        logger.error(f"Constructor prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_points_for_position(position: int) -> float:
    """Get F1 points for finishing position."""
    points_map = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
    }
    return points_map.get(position, 0)


# ── NEW: Prediction Accuracy Tracking ─────────────────────────────────────────

@router.get("/accuracy")
async def get_accuracy_stats(
    season: int = 2026,
    driver_id: Optional[str] = None,
):
    """
    Get prediction accuracy statistics.
    
    Returns Brier scores, calibration metrics, and accuracy trends.
    """
    try:
        db = next(get_db())
        
        query = db.query(PredictionModel).filter(PredictionModel.model_version.like("v3%"))
        
        if driver_id:
            query = query.filter(PredictionModel.driver_id == driver_id)
        
        predictions = query.all()
        
        if not predictions:
            return {"message": "No predictions found", "count": 0}
        
        # Calculate accuracy metrics
        evaluated = [p for p in predictions if p.brier_score is not None]
        
        if not evaluated:
            return {
                "message": "Predictions exist but not yet evaluated",
                "count": len(predictions),
            }
        
        avg_brier = sum(p.brier_score for p in evaluated) / len(evaluated)
        
        return {
            "total_predictions": len(predictions),
            "evaluated_predictions": len(evaluated),
            "avg_brier_score": round(avg_brier, 4),
            "season": season,
        }
        
    except Exception as e:
        logger.error(f"Accuracy stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── NEW: Championship Simulator ───────────────────────────────────────────────

@router.get("/championship-sim")
async def championship_simulator(
    remaining_races: int = 10,
    n_simulations: int = 5000,
):
    """
    Simulate remaining season to predict championship outcomes.
    
    Returns probability distribution for driver and constructor championships.
    """
    try:
        from data.circuit_data import get_all_circuits
        import numpy as np
        
        # Get remaining circuits
        all_circuits = get_all_circuits()
        remaining_circuits = all_circuits[:remaining_races]
        
        # Run Monte Carlo over multiple races
        driver_championship_wins = {}
        constructor_championship_wins = {}
        
        for sim in range(n_simulations):
            driver_points = {}
            constructor_points = {}
            
            for circuit in remaining_circuits:
                # Simulate race
                sim_result = predict_race(
                    circuit_id=circuit["id"],
                    n_simulations=1000,
                    seed=sim,
                )
                
                # Add points
                for driver_pred in sim_result["predictions"]:
                    pos = driver_pred["predicted_position"]
                    points = _get_points_for_position(pos)
                    
                    driver_id = driver_pred["driver_id"]
                    team = driver_pred["team"]
                    
                    driver_points[driver_id] = driver_points.get(driver_id, 0) + points
                    constructor_points[team] = constructor_points.get(team, 0) + points
            
            # Track winners
            driver_winner = max(driver_points, key=driver_points.get)
            constructor_winner = max(constructor_points, key=constructor_points.get)
            
            driver_championship_wins[driver_winner] = driver_championship_wins.get(driver_winner, 0) + 1
            constructor_championship_wins[constructor_winner] = constructor_championship_wins.get(constructor_winner, 0) + 1
        
        # Calculate probabilities
        driver_probs = {
            driver: round(count / n_simulations * 100, 2)
            for driver, count in driver_championship_wins.items()
        }
        constructor_probs = {
            team: round(count / n_simulations * 100, 2)
            for team, count in constructor_championship_wins.items()
        }
        
        # Sort by probability
        driver_probs = dict(sorted(driver_probs.items(), key=lambda x: x[1], reverse=True)[:5])
        constructor_probs = dict(sorted(constructor_probs.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return {
            "driver_championship": driver_probs,
            "constructor_championship": constructor_probs,
            "remaining_races": remaining_races,
            "simulations": n_simulations,
        }
        
    except Exception as e:
        logger.error(f"Championship simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Health Check ──────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "features": [
            "vectorized_simulation",
            "h2h_comparison",
            "constructor_predictions",
            "championship_simulator",
            "accuracy_tracking",
        ],
    }
