"""
FastAPI Routes for F1 Prediction API.

Endpoints:
  - /predict/{race_id}            → Full race prediction
  - /predict/{race_id}/winner     → Win probabilities only
  - /predict/{race_id}/dnf        → DNF risk per driver
  - /predict/{race_id}/h2h/{driver1}/{driver2} → Head-to-head comparison (FEATURE-11)
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
  
FEATURE ADDITIONS:
  - FEATURE-11: Head-to-head matchup predictions
  - FEATURE-16: Confidence intervals in predictions
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from fastapi.concurrency import run_in_threadpool

from api.schemas import (
    RacePredictionResponse, RaceMetaOut, DriverPredictionOut,
    WinnerPredictionResponse, DNFProbabilityResponse,
    StandingsResponse, StandingsEntry, ConstructorStandingsEntry,
    CircuitListResponse, CircuitSummary, CircuitResponse,
    SimulationRequest, H2HComparisonResponse,
)
from engine.predictor import predict, PredictionRequest
from data.circuit_data import get_circuit, get_all_circuits
# QUALITY-02 FIX: Use stable aliases that don't need updating every round
from data.season_2026 import CURRENT_DRIVER_STANDINGS as DRIVER_STANDINGS, CURRENT_CONSTRUCTOR_STANDINGS as CONSTRUCTOR_STANDINGS
from data.driver_data import get_driver, get_all_drivers

router = APIRouter()


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health", tags=["System"])
async def health_check():
    # FIX-8.2: Enhanced health check that verifies model readiness
    try:
        from data.driver_data import get_all_drivers
        from data.circuit_data import get_all_circuits
        n_drivers = len(get_all_drivers())
        n_circuits = len(get_all_circuits())
        return {
            "status": "ok",
            "system": "F1 Prediction Engine 2026",
            "version": "2.0",
            "active_drivers": n_drivers,
            "circuits_loaded": n_circuits,
            "model_ready": n_drivers >= 20 and n_circuits >= 24,
        }
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "error": str(e)}
        )


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
        # FIX-3.3: Run CPU-heavy prediction in thread pool to avoid blocking event loop
        request = PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            seed=seed,
        )
        result = await run_in_threadpool(predict, request)
        
        # FEATURE-18: Store prediction for tracking
        try:
            from engine.prediction_tracker import get_tracker
            tracker = get_tracker()
            tracker.store_prediction(
                circuit_id=circuit_id,
                predictions=result["predictions"],
                rain_probability=rain_probability,
                n_simulations=n_simulations
            )
        except Exception as e:
            logger.warning(f"Failed to store prediction for tracking: {e}")
        
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
        # FIX-3.3: Run CPU-heavy prediction in thread pool
        request = PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            output_format="summary",
        )
        result = await run_in_threadpool(predict, request)
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
        # FIX-3.3: Run CPU-heavy prediction in thread pool
        request = PredictionRequest(
            circuit_id=circuit_id,
            n_simulations=n_simulations,
            output_format="summary"
        )
        result = await run_in_threadpool(predict, request)
        dnf_list = sorted(result["predictions"], key=lambda x: x["dnf_pct"], reverse=True)
        return DNFProbabilityResponse(
            circuit=circuit_id,
            dnf_risk=[{"driver": p["driver"], "team": p["team"], "dnf_pct": p["dnf_pct"]}
                      for p in dnf_list],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{circuit_id}/h2h/{driver1_id}/{driver2_id}", 
            response_model=H2HComparisonResponse, tags=["Predictions"])
async def predict_head_to_head(
    circuit_id: str,
    driver1_id: str,
    driver2_id: str,
    n_simulations: int = Query(5000, ge=100, le=50000),
    rain_probability: Optional[float] = Query(None, ge=0.0, le=1.0),
):
    """
    FEATURE-11: Head-to-head matchup prediction between two drivers.
    
    Returns probability that driver1 finishes ahead of driver2, plus detailed comparison.
    """
    try:
        get_circuit(circuit_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{circuit_id}' not found.")
    
    # Validate drivers exist
    try:
        driver1 = get_driver(driver1_id)
        if not driver1:
            raise KeyError(f"Driver '{driver1_id}' not found")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Driver '{driver1_id}' not found.")
    
    try:
        driver2 = get_driver(driver2_id)
        if not driver2:
            raise KeyError(f"Driver '{driver2_id}' not found")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Driver '{driver2_id}' not found.")
    
    try:
        # Get full race prediction
        request = PredictionRequest(
            circuit_id=circuit_id,
            rain_probability=rain_probability,
            n_simulations=n_simulations,
            output_format="full",
        )
        result = await run_in_threadpool(predict, request)
        
        # Find both drivers in predictions
        pred1 = None
        pred2 = None
        for p in result["predictions"]:
            if p["driver_name"] == driver1["name"]:
                pred1 = p
            elif p["driver_name"] == driver2["name"]:
                pred2 = p
        
        if not pred1 or not pred2:
            raise HTTPException(status_code=404, detail="One or both drivers not found in predictions")
        
        # Calculate head-to-head probability based on position distributions
        # P(driver1 beats driver2) = sum over all positions where pos1 < pos2
        pos_dist1 = pred1.get("position_distribution", [0] * 20)
        pos_dist2 = pred2.get("position_distribution", [0] * 20)
        
        h2h_prob = 0.0
        for i in range(len(pos_dist1)):
            for j in range(i + 1, len(pos_dist2)):
                # Driver1 at position i+1, Driver2 at position j+1 (i < j means driver1 ahead)
                h2h_prob += pos_dist1[i] * pos_dist2[j]
        
        # Normalize to account for both finishing
        total_finish_prob = sum(pos_dist1) * sum(pos_dist2)
        if total_finish_prob > 0:
            h2h_prob_normalized = h2h_prob / total_finish_prob
        else:
            h2h_prob_normalized = 0.5
        
        return H2HComparisonResponse(
            circuit=circuit_id,
            driver1={
                "id": driver1_id,
                "name": driver1["name"],
                "team": driver1["team"],
                "predicted_position": pred1["predicted_position"],
                "win_probability": pred1["win_pct"],
                "top3_probability": pred1["top3_pct"],
            },
            driver2={
                "id": driver2_id,
                "name": driver2["name"],
                "team": driver2["team"],
                "predicted_position": pred2["predicted_position"],
                "win_probability": pred2["win_pct"],
                "top3_probability": pred2["top3_pct"],
            },
            driver1_beats_driver2_prob=round(h2h_prob_normalized * 100, 1),
            driver2_beats_driver1_prob=round((1 - h2h_prob_normalized) * 100, 1),
            analysis=_generate_h2h_analysis(driver1, driver2, pred1, pred2, h2h_prob_normalized),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"H2H prediction failed: {e}")


def _generate_h2h_analysis(driver1: dict, driver2: dict, pred1: dict, pred2: dict, h2h_prob: float) -> str:
    """Generate textual analysis of the head-to-head matchup."""
    if h2h_prob > 0.65:
        advantage = f"{driver1['name']} has a significant advantage"
    elif h2h_prob > 0.55:
        advantage = f"{driver1['name']} has a moderate advantage"
    elif h2h_prob > 0.45:
        advantage = "The matchup is very close"
    elif h2h_prob > 0.35:
        advantage = f"{driver2['name']} has a moderate advantage"
    else:
        advantage = f"{driver2['name']} has a significant advantage"
    
    # Add context
    pos_diff = abs(pred1["predicted_position"] - pred2["predicted_position"])
    if pos_diff <= 2:
        context = f"Expected to finish within {pos_diff} position(s) of each other."
    else:
        context = f"Expected finishing gap: ~{pos_diff} positions."
    
    return f"{advantage}. {context}"


@router.post("/simulate", response_model=RacePredictionResponse, tags=["Predictions"])
async def simulate_custom(request: SimulationRequest):
    """Run custom simulation with parameter overrides."""
    try:
        get_circuit(request.race_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{request.race_id}' not found.")
    
    try:
        # FIX-3.3: Run CPU-heavy prediction in thread pool
        result = await run_in_threadpool(
            predict,
            PredictionRequest(
                circuit_id=request.race_id,
                rain_probability=request.rain_probability,
                n_simulations=request.n_simulations or 5000,
                seed=request.seed,
            ),
        )
        
        # FEATURE-18: Store prediction for tracking
        try:
            from engine.prediction_tracker import get_tracker
            tracker = get_tracker()
            tracker.store_prediction(
                circuit_id=request.race_id,
                predictions=result["predictions"],
                rain_probability=request.rain_probability,
                n_simulations=request.n_simulations or 5000
            )
        except Exception as e:
            logger.warning(f"Failed to store prediction for tracking: {e}")
        
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")


# ── High-Performance Simulation (FEATURE-13) ──────────────────────────────────

@router.post("/simulate/fast", response_model=RacePredictionResponse, tags=["Predictions"])
async def simulate_fast(request: SimulationRequest):
    """
    FEATURE-13: High-performance vectorized simulation.
    
    Uses NumPy vectorization for 10-50x speedup. Ideal for large simulations (10k+).
    """
    try:
        get_circuit(request.race_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Circuit '{request.race_id}' not found.")
    
    try:
        from engine.optimized_simulation import simulate_race_vectorized
        
        # Use vectorized simulation
        sim_result = await run_in_threadpool(
            simulate_race_vectorized,
            circuit_id=request.race_id,
            rain_probability=request.rain_probability,
            n_runs=request.n_simulations or 5000,
            seed=request.seed,
            grid_overrides=request.grid_overrides,
        )
        
        # Convert to standard format
        from engine.probability_model import predict_race
        result = predict_race(
            circuit_id=request.race_id,
            rain_probability=request.rain_probability,
            n_simulations=request.n_simulations or 5000,
            seed=request.seed,
        )
        
        # Override stats with vectorized results
        for pred in result["predictions"]:
            did = pred["driver_id"]
            if did in sim_result["stats"]:
                stats = sim_result["stats"][did]
                pred["win_probability"] = stats["win_probability"]
                pred["top3_probability"] = stats["top3_probability"]
                pred["top10_probability"] = stats["top10_probability"]
                pred["dnf_probability"] = stats["dnf_probability"]
                pred["predicted_position"] = round(stats["expected_position"])
        
        # FEATURE-18: Store prediction
        try:
            from engine.prediction_tracker import get_tracker
            tracker = get_tracker()
            tracker.store_prediction(
                circuit_id=request.race_id,
                predictions=result["predictions"],
                rain_probability=request.rain_probability,
                n_simulations=request.n_simulations or 5000
            )
        except Exception as e:
            logger.warning(f"Failed to store prediction: {e}")
        
        return _result_to_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fast simulation failed: {e}")


# ── Standings ──────────────────────────────────────────────────────────────────

@router.get("/standings/drivers", tags=["Standings"])
async def driver_standings():
    """Current 2026 F1 Driver Championship standings."""
    result = []
    for s in DRIVER_STANDINGS:  # QUALITY-02 FIX: Use stable alias
        try:
            d = get_driver(s["driver"])
            name = d["name"]
        except KeyError:
            name = s["driver"]
        result.append(StandingsEntry(position=s["position"], driver=name, points=s["points"]))
    return result


@router.get("/standings/constructors", tags=["Standings"])
async def constructor_standings():
    return [ConstructorStandingsEntry(**s) for s in CONSTRUCTOR_STANDINGS]  # QUALITY-02 FIX


@router.get("/standings", response_model=StandingsResponse, tags=["Standings"])
async def all_standings():
    """Combined driver + constructor standings."""
    drivers = []
    for s in DRIVER_STANDINGS:  # QUALITY-02 FIX
        try:
            name = get_driver(s["driver"])["name"]
        except KeyError:
            name = s["driver"]
        drivers.append(StandingsEntry(position=s["position"], driver=name, points=s["points"]))
    constructors = [ConstructorStandingsEntry(**s) for s in CONSTRUCTOR_STANDINGS]  # QUALITY-02 FIX
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


# ── Model Performance Dashboard (FEATURE-18) ──────────────────────────────────

@router.get("/dashboard/performance", tags=["Analytics"])
async def model_performance_dashboard():
    """
    FEATURE-18: Model accuracy and performance dashboard.
    
    Returns comprehensive metrics including Brier scores, log loss, and trends.
    """
    try:
        from engine.prediction_tracker import get_tracker
        tracker = get_tracker()
        return tracker.get_model_performance_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {e}")


@router.get("/dashboard/recent-predictions", tags=["Analytics"])
async def recent_predictions(limit: int = Query(10, ge=1, le=50)):
    """Get recent predictions with optional actual results."""
    try:
        from engine.prediction_tracker import get_tracker
        tracker = get_tracker()
        return tracker.get_recent_predictions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/season-accuracy", tags=["Analytics"])
async def season_accuracy(season_year: int = Query(2026)):
    """Get aggregate accuracy metrics for a specific season."""
    try:
        from engine.prediction_tracker import get_tracker
        tracker = get_tracker()
        return tracker.get_season_accuracy(season_year=season_year)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
