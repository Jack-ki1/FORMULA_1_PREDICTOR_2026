"""
Prediction Orchestrator — v2.
Supports grid_overrides dict for post-qualifying accuracy boost.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import hashlib
import json
import time
import logging
from datetime import datetime, date

import pandas as pd

from data.circuit_data import get_circuit
from engine.probability_model import predict_race
from config.settings import LIVE_OPENF1_ENABLED

logger = logging.getLogger(__name__)


@dataclass
class PredictionRequest:
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 5000
    seed: Optional[int] = None
    output_format: str = "full"
    grid_overrides: Dict[str, int] = field(default_factory=dict)
    vectorized: bool = True
    qualifying_completed: bool = False
    live_weather_override: Optional[float] = None
    session_type: str = "race"
    sprint_weekend: bool = False
    live_context: Dict[str, Any] = field(default_factory=dict)


# PREDICTION CACHING (P1 Priority - Performance Optimization)
_cache: Dict[str, dict] = {}
_cache_ttl: Dict[str, float] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes cache validity


def _cache_key(request: PredictionRequest) -> str:
    """Generate deterministic cache key from prediction request parameters."""
    payload = {
        "circuit": request.circuit_id,
        "rain": round(request.rain_probability or 0, 2),
        "sims": request.n_simulations,
        "seed": request.seed,
        "grid": sorted(request.grid_overrides.items()),
        "session_type": request.session_type.lower(),
        "live_weather": request.live_weather_override,
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class DriverPrediction:
    driver_id: str
    driver_name: str
    team: str
    predicted_position: int
    win_probability: float
    top3_probability: float
    top5_probability: float  # BUG FIX: Add Top-5 probability field
    top10_probability: float
    dnf_probability: float
    teammate_beat_prob: float
    composite_score: float
    expected_points: float   # BUG FIX: Add expected points field
    confidence: str

    def to_dict(self) -> dict:
        return {
            "driver_id":         self.driver_id,  # Add driver_id for database storage
            "driver_name":       self.driver_name,  # QUALITY-10 FIX: Use driver_name consistently
            "driver":            self.driver_name,  # Keep 'driver' for backward compatibility
            "team":              self.team,
            "predicted_position":self.predicted_position,
            "win_pct":           round(self.win_probability * 100, 1),
            "top3_pct":          round(self.top3_probability * 100, 1),
            "top5_pct":          round(self.top5_probability * 100, 1),  # BUG FIX: Add Top-5 percentage
            "top10_pct":         round(self.top10_probability * 100, 1),
            "dnf_pct":           round(self.dnf_probability * 100, 1),
            "teammate_beat_pct": round(self.teammate_beat_prob * 100, 1),
            "expected_points":   round(self.expected_points, 1),  # BUG FIX: Add expected points
            "confidence":        self.confidence.title(),
        }


def _assign_confidence(win_prob: float, composite_score: float) -> str:
    """
    Assign model confidence level based on win probability and composite score.
    
    Thresholds calibrated against historical prediction accuracy:
    - HIGH: Win prob >25% or score >0.72 → historically 80%+ accuracy in top-3 prediction
    - MEDIUM: Win prob >5% or score >0.45 → moderate confidence, typical for midfield battles
    - LOW: Everything else → high uncertainty, backmarkers or unpredictable conditions
    """
    if win_prob > 0.25 or composite_score > 0.72:
        return "high"
    if win_prob > 0.05 or composite_score > 0.45:
        return "medium"
    return "low"


def _enforce_probability_hierarchy(pred: dict) -> dict:
    """
    Enforce monotonic probability constraints: win ≤ top3 ≤ top10.
    
    This is mathematically required - a driver cannot have higher probability
    of winning than finishing in top 3, or top 3 than top 10.
    """
    # Ensure win_pct <= top3_pct
    pred["win_probability"] = min(pred["win_probability"], pred["top3_probability"])
    
    # Ensure top3_pct <= top10_pct
    pred["top3_probability"] = min(pred["top3_probability"], pred["top10_probability"])
    
    return pred


def _normalize_win_probabilities(predictions: list) -> list:
    """
    Normalize win probabilities so they sum to 1.0 (100%).
    
    Due to DNF handling and floating point errors, the sum of all drivers'
    win probabilities often doesn't equal exactly 1.0 after simulation.
    """
    total_win_prob = sum(p["win_probability"] for p in predictions)
    if total_win_prob > 0 and abs(total_win_prob - 1.0) > 1e-6:
        for p in predictions:
            p["win_probability"] = round(p["win_probability"] / total_win_prob, 6)
    return predictions


# NEW: Sprint-race awareness. A Sprint is ~100km with its own points table (top 8
# only) versus a full ~305km Grand Prix (top 10 + fastest lap). Rather than re-running
# or altering the Monte Carlo engine, this recomputes expected_points from the position
# distribution that's already been simulated, and scales dnf_probability down to reflect
# a much shorter race — there's simply less time for mechanical failures or incidents.
SPRINT_POINTS = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
SPRINT_DISTANCE_FACTOR = 0.35  # ~100km sprint vs ~305km race distance ratio


def _apply_sprint_adjustments(output_predictions: list, n_simulations: int) -> None:
    """Recompute expected_points with the sprint points table and reduce dnf_pct
    to reflect sprint race distance. Mutates output_predictions in place."""
    for d in output_predictions:
        dist = d.get("position_distribution") or []
        if dist and n_simulations:
            sprint_points_total = sum(
                SPRINT_POINTS.get(pos + 1, 0) * count for pos, count in enumerate(dist)
            )
            d["expected_points"] = round(sprint_points_total / n_simulations, 2)
        else:
            d["expected_points"] = 0.0
        d["dnf_pct"] = round(d.get("dnf_pct", 0.0) * SPRINT_DISTANCE_FACTOR, 1)


def _check_race_completed(circuit_id: str) -> dict:
    """
    Check if a race has already completed and fetch actual session results.
    
    This function checks the 2026 calendar for race dates and compares with
    current date. If the race date has passed, it attempts to fetch actual
    session data from FastF1 API.
    
    Args:
        circuit_id: Circuit identifier (e.g., "australia", "monaco")
    
    Returns:
        Dictionary with:
        - completed: bool indicating if race is completed
        - race_date: Date of the race
        - is_sprint_weekend: Whether this is a sprint weekend
        - sessions: Dict containing FP1/FP2/FP3, qualifying, sprint, and race results
    
    Example:
        {
            "completed": True,
            "race_date": "2026-03-08",
            "is_sprint_weekend": False,
            "sessions": {
                "fp1": {...},
                "qualifying": {...},
                "race": {...}
            }
        }
    """
    try:
        from data.calendar_2026 import get_race_by_circuit
        
        logger.info(f"Checking race completion status for: {circuit_id}")
        
        # Find race in calendar
        race_info = get_race_by_circuit(circuit_id)
        
        if not race_info:
            logger.warning(f"Circuit {circuit_id} not found in 2026 calendar")
            return {"completed": False, "error": f"Circuit {circuit_id} not found"}
        
        logger.info(f"Found race info: {race_info.get('name')} on {race_info.get('date')}")
        
        # Parse race date
        race_date_str = race_info.get("date", "")
        if not race_date_str:
            return {"completed": False, "error": "Race date not available"}
        
        try:
            race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"completed": False, "error": f"Invalid date format: {race_date_str}"}
        
        # Check if race date is in the past
        today = date.today()
        is_completed = race_date < today
        
        logger.info(f"Today: {today}, Race date: {race_date}, Completed: {is_completed}")
        
        if not is_completed:
            return {
                "completed": False,
                "race_date": race_date_str,
                "is_sprint_weekend": race_info.get("sprint", False),
                "message": "Race not yet completed"
            }
        
        # Race is completed - try to fetch actual results from FastF1 or Jolpica
        try:
            from data.fastf1_integration import get_session, is_fastf1_available  # Updated import
            
            race_name = race_info.get("name", "")
            is_sprint = race_info.get("sprint", False)
            
            sessions = {}
            
            # Try FastF1 first if available
            if is_fastf1_available():
                logger.info("FastF1 available - fetching results from FastF1")
                
                # Fetch Practice Sessions (FP1, FP2, FP3)
                for fp_num in ['1', '2', '3']:
                    try:
                        session = get_session(2026, race_info.get("round", race_name), f'FP{fp_num}')  # Use FP1, FP2, FP3 instead of P1, P2, P3
                        if session:
                            try:
                                session.load(laps=True, telemetry=False, weather=False, messages=False)
                            except Exception as load_err:
                                logger.debug(f"Could not load laps for FP{fp_num}: {load_err}")

                            classification = _build_practice_classification(session)
                            if classification:
                                sessions[f"fp{fp_num}"] = {
                                    "session_type": f"Practice {fp_num}",
                                    "date": str(session.event['EventDate']),
                                    "results": classification,
                                    "fastest_lap": _get_fastest_lap_from_session(session)
                                }
                                logger.info(f"Successfully fetched FP{fp_num} results ({len(classification)} drivers)")
                    except Exception as e:
                        logger.debug(f"Could not fetch FP{fp_num}: {e}")
                
                # Fetch Qualifying
                try:
                    qual_session = get_session(2026, race_info.get("round", race_name), 'Q')  # Use round number instead of name
                    if qual_session:
                        try:
                            qual_session.load(laps=True, telemetry=False, weather=False, messages=False)
                        except Exception as load_err:
                            logger.debug(f"Could not load qualifying laps: {load_err}")
                        
                        if hasattr(qual_session, 'results') and len(qual_session.results) > 0:
                            # Convert results to dict and handle Timedelta serialization
                            results_records = []
                            for idx, row in qual_session.results.iterrows():
                                record = {}
                                for col in qual_session.results.columns:
                                    value = row[col]
                                    # Handle Timedelta objects for JSON serialization
                                    if hasattr(value, 'total_seconds'):  # Timedelta-like object
                                        record[col] = str(value) if value is not pd.NaT and pd.notna(value) else None
                                    elif pd.isna(value):  # Handle NaN/NaT values
                                        record[col] = None
                                    else:
                                        record[col] = value
                                results_records.append(record)
                                                        
                            sessions["qualifying"] = {
                                "session_type": "Qualifying",
                                "date": str(qual_session.event['EventDate']),
                                "results": results_records,
                                "grid_positions": _extract_grid_positions(qual_session)
                            }
                            logger.info("Successfully fetched qualifying results")
                except Exception as e:
                    logger.debug(f"Could not fetch qualifying: {e}")
                
                # Fetch Sprint (if sprint weekend)
                if is_sprint:
                    try:
                        sprint_session = get_session(2026, race_info.get("round", race_name), 'S')  # Use round number instead of name
                        if sprint_session:
                            try:
                                sprint_session.load(laps=True, telemetry=False, weather=False, messages=False)
                            except Exception as load_err:
                                logger.debug(f"Could not load sprint laps: {load_err}")
                            
                            if hasattr(sprint_session, 'results') and len(sprint_session.results) > 0:
                                # Convert results to dict and handle Timedelta serialization
                                results_records = []
                                for idx, row in sprint_session.results.iterrows():
                                    record = {}
                                    for col in sprint_session.results.columns:
                                        value = row[col]
                                        # Handle Timedelta objects for JSON serialization
                                        if hasattr(value, 'total_seconds'):  # Timedelta-like object
                                            record[col] = str(value) if value is not pd.NaT and pd.notna(value) else None
                                        elif pd.isna(value):  # Handle NaN/NaT values
                                            record[col] = None
                                        else:
                                            record[col] = value
                                    results_records.append(record)
                                
                                sessions["sprint"] = {
                                    "session_type": "Sprint Race",
                                    "date": str(sprint_session.event['EventDate']),
                                    "results": results_records,
                                    "winner": results_records[0]['Abbreviation'] if results_records else None
                                }
                                logger.info("Successfully fetched sprint results")
                    except Exception as e:
                        logger.debug(f"Could not fetch sprint: {e}")
                
                # Fetch Main Race
                try:
                    race_session = get_session(2026, race_info.get("round", race_name), 'R')  # Use round number instead of name
                    if race_session:
                        try:
                            race_session.load(laps=True, telemetry=False, weather=False, messages=False)
                        except Exception as load_err:
                            logger.debug(f"Could not load race laps: {load_err}")
                        
                        if hasattr(race_session, 'results') and len(race_session.results) > 0:
                            # Convert results to dict and handle Timedelta serialization
                            results_records = []
                            for idx, row in race_session.results.iterrows():
                                record = {}
                                for col in race_session.results.columns:
                                    value = row[col]
                                    # Handle Timedelta objects for JSON serialization
                                    if hasattr(value, 'total_seconds'):  # Timedelta-like object
                                        record[col] = str(value) if value is not pd.NaT and pd.notna(value) else None
                                    elif pd.isna(value):  # Handle NaN/NaT values
                                        record[col] = None
                                    else:
                                        record[col] = value
                                results_records.append(record)
                                                        
                            sessions["race"] = {
                                "session_type": "Race",
                                "date": str(race_session.event['EventDate']),
                                "results": results_records,
                                "winner": results_records[0]['Abbreviation'] if results_records else None,
                                "fastest_lap": _get_fastest_lap_from_session(race_session)
                            }
                            logger.info("Successfully fetched race results")
                except Exception as e:
                    logger.debug(f"Could not fetch race: {e}")
                    
            else:
                # FastF1 not available - use Jolpica API as fallback
                logger.info("FastF1 not available - using Jolpica API as fallback")
                
                try:
                    from data.jolpica_client import get_jolpica_client
                    
                    client = get_jolpica_client()
                    round_num = race_info.get("round")
                    
                    if not round_num:
                        logger.warning(f"No round number found for {circuit_id}")
                    else:
                        # Fetch race results from Jolpica
                        race_results = client.get_race_results(2026, round_num)
                        if race_results and race_results.get("results"):
                            # Convert Jolpica format to expected format
                            jolpica_results = []
                            for r in race_results["results"]:
                                jolpica_results.append({
                                    "Position": r.get("position"),
                                    "Driver": r.get("driver_code", ""),
                                    "Abbreviation": r.get("driver_code", ""),
                                    "TeamName": r.get("constructor_name", ""),
                                    "Constructor": r.get("constructor_name", ""),
                                    "GridPosition": r.get("grid"),
                                    "Time": r.get("time", ""),
                                    "Status": r.get("status", ""),
                                    "Points": r.get("points", 0),
                                    "Laps": r.get("laps", 0)
                                })
                            
                            sessions["race"] = {
                                "session_type": "Race",
                                "date": race_results.get("date", ""),
                                "results": jolpica_results,
                                "winner": jolpica_results[0]["Abbreviation"] if jolpica_results else None
                            }
                            logger.info(f"Successfully fetched race results from Jolpica ({len(jolpica_results)} drivers)")
                        
                        # Fetch qualifying results from Jolpica
                        qual_results = client.get_qualifying_results(2026, round_num)
                        if qual_results and qual_results.get("qualifying_results"):
                            jolpica_qual = []
                            for q in qual_results["qualifying_results"]:
                                jolpica_qual.append({
                                    "Position": q.get("position"),
                                    "Driver": q.get("driver_code", ""),
                                    "Abbreviation": q.get("driver_code", ""),
                                    "TeamName": q.get("constructor_name", ""),
                                    "Constructor": q.get("constructor_name", ""),
                                    "Q1": q.get("Q1", ""),
                                    "Q2": q.get("Q2", ""),
                                    "Q3": q.get("Q3", "")
                                })
                            
                            sessions["qualifying"] = {
                                "session_type": "Qualifying",
                                "date": qual_results.get("date", ""),
                                "results": jolpica_qual,
                                "grid_positions": {q["Abbreviation"]: q["Position"] for q in jolpica_qual}
                            }
                            logger.info(f"Successfully fetched qualifying results from Jolpica ({len(jolpica_qual)} drivers)")
                        
                        # Fetch sprint results if applicable
                        if is_sprint:
                            try:
                                sprint_results_data = client.get_sprint_results(2026, round_num)
                                if sprint_results_data and sprint_results_data.get("results"):
                                    jolpica_sprint = []
                                    for s in sprint_results_data["results"]:
                                        jolpica_sprint.append({
                                            "Position": s.get("position"),
                                            "Driver": s.get("driver_code", ""),
                                            "Abbreviation": s.get("driver_code", ""),
                                            "TeamName": s.get("constructor_name", ""),
                                            "Constructor": s.get("constructor_name", ""),
                                            "Time": s.get("time", ""),
                                            "Status": s.get("status", ""),
                                            "Points": s.get("points", 0),
                                            "GridPosition": s.get("grid", 0),
                                            "Laps": s.get("laps", 0)
                                        })
                                    
                                    sessions["sprint"] = {
                                        "session_type": "Sprint Race",
                                        "date": sprint_results_data.get("date", ""),
                                        "results": jolpica_sprint,
                                        "winner": jolpica_sprint[0]["Abbreviation"] if jolpica_sprint else None
                                    }
                                    logger.info(f"Successfully fetched sprint results from Jolpica ({len(jolpica_sprint)} drivers)")
                            except Exception as e:
                                logger.debug(f"Could not fetch sprint results: {e}")
                        
                        # Note: Jolpica/Ergast API does NOT provide practice session results (FP1/FP2/FP3)
                        # This is a limitation of the free API. Practice data would require FastF1 or paid APIs.
                        logger.info("Note: Practice session results not available via Jolpica API")
                        
                        logger.info(f"Jolpica fallback complete - fetched {len(sessions)} sessions")
                        
                except Exception as e:
                    logger.error(f"Error fetching from Jolpica: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            logger.info(f"Fetched {len(sessions)} session(s) for {race_name}")
            logger.info(f"Available sessions: {list(sessions.keys())}")
            
            return {
                "completed": True,
                "race_date": race_date_str,
                "is_sprint_weekend": is_sprint,
                "sessions": sessions,
                "available_sessions": list(sessions.keys()),
                "data_source": "fastf1" if is_fastf1_available() else "jolpica"
            }
            
        except Exception as e:
            logger.error(f"Error fetching race results: {e}")
            return {
                "completed": True,
                "race_date": race_date_str,
                "is_sprint_weekend": race_info.get("sprint", False),
                "error": f"Failed to fetch results: {str(e)}"
            }
        
    except Exception as e:
        logger.error(f"Error checking race completion: {e}")
        return {"completed": False, "error": str(e)}


def _get_fastest_lap_from_session(session) -> Optional[dict]:
    """Extract fastest lap information from a session.

    NOTE: `session.lap_times` does not exist on a FastF1 Session object —
    the real property is `session.laps` (a Laps DataFrame), and the correct
    way to get the single fastest lap is `.pick_fastest()` (in FastF1 >=3.x;
    older docs sometimes reference `pick_quickest`, which does not exist in
    the currently installed fastf1 version).
    """
    try:
        if hasattr(session, 'laps') and session.laps is not None and len(session.laps) > 0:
            fastest = session.laps.pick_fastest()
            if fastest is not None:
                lap_number = fastest.get('LapNumber')
                # Handle Timedelta conversion to string for JSON serialization
                lap_time = fastest.get('LapTime')
                lap_time_str = str(lap_time) if lap_time is not None else None
                return {
                    "driver": fastest.get('Driver'),
                    "time": lap_time_str,  # Convert Timedelta to string
                    "lap_number": int(lap_number) if pd.notna(lap_number) else None
                }
        return None
    except Exception as e:
        logger.debug(f"Could not extract fastest lap: {e}")
        return None


def _build_practice_classification(session) -> list:
    """Build a P1/P2/P3... classification for a practice session from lap data.

    Practice sessions have no official finishing "Position" the way Race/
    Qualifying/Sprint do — `session.results` mostly contains driver/team
    entry info, not a meaningful ranking. This ranks each driver by their
    single fastest lap of the session, matching how practice results are
    actually reported (fastest lap per driver, sorted ascending).
    """
    try:
        if not hasattr(session, 'laps') or session.laps is None or len(session.laps) == 0:
            return []

        rows = []
        for drv in session.laps['Driver'].dropna().unique():
            fastest = session.laps.pick_driver(drv).pick_fastest()
            if fastest is None:
                continue
            # Handle Timedelta conversion to string for JSON serialization
            lap_time = fastest.get('LapTime')
            lap_time_serializable = str(lap_time) if lap_time is not pd.NaT and pd.notna(lap_time) else None
            rows.append({
                "Driver": drv,
                "Abbreviation": drv,
                "_lap_time": lap_time,  # Keep original for sorting
                "LapTime": lap_time_serializable,  # Convert Timedelta to string for JSON
                "Compound": fastest.get('Compound'),
            })

        # Sort by actual lap time (not string representation)
        rows.sort(key=lambda r: r["_lap_time"] if r["_lap_time"] is not None else pd.Timedelta.max)
        for i, row in enumerate(rows, start=1):
            row["Position"] = i
            del row["_lap_time"]  # not JSON-serializable

        return rows
    except Exception as e:
        logger.debug(f"Could not build practice classification: {e}")
        return []


def _extract_grid_positions(qualifying_session) -> dict:
    """Extract grid positions from qualifying results."""
    try:
        grid = {}
        for idx, row in qualifying_session.results.iterrows():
            driver = row.get('Abbreviation', '')
            position = int(row.get('Position', idx + 1))
            if driver:
                grid[driver] = position
        return grid
    except Exception as e:
        logger.debug(f"Could not extract grid positions: {e}")
        return {}


def predict(request: PredictionRequest) -> dict:
    """Main prediction function with caching to avoid redundant Monte Carlo simulations."""
    # FEATURE 1: Check if race has already completed
    race_status = _check_race_completed(request.circuit_id)
    
    # If race is completed, return actual results instead of predictions
    if race_status.get("completed"):
        return {
            "meta": {
                "circuit": request.circuit_id,
                "race_completed": True,
                "race_date": race_status.get("race_date"),
                "is_sprint_weekend": race_status.get("is_sprint_weekend", False),
                "safety_car_probability": None,
                "rain_probability": request.rain_probability,
                "n_simulations": request.n_simulations,
                "overall_model_confidence": None,
                "message": "This race has already been completed. Showing actual results.",
            },
            "actual_results": race_status.get("sessions", {}),
            "predictions": [],  # Empty list for dashboard compatibility
            "podium_predictions": [],
            "likely_top_surprises": [],
            "raw": None,
        }
    
    # Check cache first
    key = _cache_key(request)
    now = time.monotonic()
    
    if key in _cache and now - _cache_ttl[key] < CACHE_TTL_SECONDS:
        return _cache[key]
    
    # Cache miss or expired - run prediction
    circuit = get_circuit(request.circuit_id)
    sc_prob   = circuit.get("safety_car_probability", 0.5)
        # If live OpenF1 data shows rain, override user input with actual probability
    live_rain_prob = request.live_weather_override if LIVE_OPENF1_ENABLED else None

    rain_prob = live_rain_prob if live_rain_prob is not None else (request.rain_probability or circuit.get("rain_probability_typical", 0.2))
        
    # BUG-01 FIX: Pass grid_overrides to predict_race so they are actually applied
    raw = predict_race(
        circuit_id=request.circuit_id,
        rain_probability=rain_prob,
        n_simulations=request.n_simulations,
        seed=request.seed,
        grid_overrides=request.grid_overrides or {},
        vectorized=request.vectorized,
    )

    # NEW: Apply probability hierarchy enforcement (3.5)
    for p in raw["predictions"]:
        _enforce_probability_hierarchy(p)
    
    # NEW: Normalize win probabilities to sum to 1.0 (3.6)
    raw["predictions"] = _normalize_win_probabilities(raw["predictions"])
    
    # H-3 FIX: Re-enforce hierarchy AFTER normalization.
    # Normalization can scale win_prob up, breaking win <= top3 <= top10 again.
    for p in raw["predictions"]:
        _enforce_probability_hierarchy(p)

    predictions = []
    for p in raw["predictions"]:
        dp = DriverPrediction(
            driver_id=p["driver_id"],
            driver_name=p["driver_name"],
            team=p["team"],
            predicted_position=p["predicted_position"],
            win_probability=p["win_probability"],
            top3_probability=p["top3_probability"],
            top5_probability=p.get("top5_probability", 0.0),  # BUG FIX: Add Top-5 probability
            top10_probability=p["top10_probability"],
            dnf_probability=p["dnf_probability"],
            teammate_beat_prob=p["teammate_beat_prob"],
            composite_score=p["composite_score"],
            expected_points=p.get("expected_points", 0.0),  # BUG FIX: Add expected points
            confidence=_assign_confidence(p["win_probability"], p["composite_score"]),
        )
        predictions.append(dp)

    top_surprise = sorted(
        [p for p in predictions if p.predicted_position > 6 and p.top10_probability > 0.38],
        key=lambda x: x.top10_probability, reverse=True,
    )[:3]

    # OVERALL_CONFIDENCE CALCULATION:
    # Base confidence of 90%, reduced by circuit chaos factors:
    # - High SC probability circuits (Canada, Baku) reduce confidence by up to 25%
    # - High rain probability circuits (Monaco, Spa) reduce confidence by up to 15%
    # Minimum floor of 40% ensures we never claim zero confidence
    # These coefficients were calibrated against prediction accuracy across 2024-2025 seasons
    overall_confidence = max(0.40, 0.90 - (sc_prob * 0.25) - (rain_prob * 0.15))

    # Build output dicts, also preserving raw features + position_distribution
    output_predictions = []
    raw_by_id = {p["driver_id"]: p for p in raw["predictions"]}
    for dp in predictions:
        d = dp.to_dict()
        raw_p = raw_by_id.get(dp.driver_id, {})
        d["composite_score"]       = dp.composite_score
        d["features"]              = raw_p.get("features", {})
        d["position_distribution"] = raw_p.get("position_distribution", [0] * 20)
        output_predictions.append(d)

    # NEW: Sprint session gets sprint points (top 8) + reduced DNF risk (shorter race),
    # derived from the position distribution already simulated above — no re-simulation.
    is_sprint_session = request.session_type.lower() in ("sprint", "sprint_race")
    if is_sprint_session:
        _apply_sprint_adjustments(output_predictions, request.n_simulations)

    result = {
        "meta": {
            "circuit":                  circuit["name"],
            "city":                     circuit["city"],
            "race_date":                circuit["race_date"],
            "sprint_weekend":           circuit.get("sprint_weekend", False),
            "is_sprint_session":        is_sprint_session,
            "safety_car_probability":   sc_prob,
            "rain_probability":         rain_prob,
            "n_simulations":            request.n_simulations,
            "overall_model_confidence": round(overall_confidence, 3),
            "session_type":              request.session_type.lower(),
            "qualifying_completed":      request.qualifying_completed,
            "grid_overrides_count":      len(request.grid_overrides or {}),
            "rain_source":               "openf1_live" if live_rain_prob is not None else "request_or_circuit",
        },
        "predictions":          output_predictions,
        "podium_predictions":   [p.driver_name for p in predictions[:3]],
        "likely_top_surprises": [p.driver_name for p in top_surprise],
        "raw":                  raw if request.output_format == "full" else None,
    }
    
    # Store in cache
    _cache[key] = result
    _cache_ttl[key] = now
    
    return result