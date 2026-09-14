"""
Main predictor orchestrator - coordinates features, models, Monte Carlo simulations,
and probability shaping for multi-session and multi-target predictions.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.config.settings import settings
from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.data.calendar_2026 import get_race_by_id, CALENDAR_2026
from backend.app.models.prediction import Prediction
from backend.app.database.client import DatabaseClient
from backend.app.engine.grid_model import GridModel
from backend.app.engine.monte_carlo import MonteCarloSimulator
from backend.app.engine.ai_client import ai_client
from backend.app.engine.probability_model import (
    probability_model,
    enforce_probability_sum,
    calibrate_probabilities,
    calculate_confidence_intervals,
    detect_model_drift,
    save_prediction_metadata,
)
from backend.app.cache.redis import get_cache

logger = logging.getLogger(__name__)


def _strength_based_grid(all_drivers: List[Dict]) -> Dict[str, int]:
    """
    Build a simulated qualifying grid ordered by driver strength + small noise.
    Used when no real qualifying data or manual override is available.
    """
    rng = np.random.default_rng()
    scores = []
    for d in all_drivers:
        strength = d.get("strength", 50) / 100.0
        noise = rng.normal(0, 0.04)
        scores.append((d["code"], strength + noise))
    scores.sort(key=lambda x: x[1], reverse=True)
    return {code: pos for pos, (code, _) in enumerate(scores, start=1)}


def _apply_chaos_smoothing(probs: Dict[str, float], chaos_level: float) -> Dict[str, float]:
    """
    Lightly flatten / sharpen probabilities based on chaos level using a linear
    blend toward uniform — never uses power-law on already-normalised probabilities.
    chaos_level=0   -> preserve as-is (no flattening)
    chaos_level=50  -> mild 30% blend toward uniform
    chaos_level=100 -> strong 60% blend toward uniform
    """
    if not probs:
        return probs
    n = len(probs)
    uniform = 1.0 / n
    flatten_factor = 0.6 * (chaos_level / 100.0)
    result = {
        code: (1 - flatten_factor) * p + flatten_factor * uniform
        for code, p in probs.items()
    }
    total = sum(result.values())
    if total > 0:
        result = {c: v / total for c, v in result.items()}
    return result


def _build_summary(
    probabilities: Dict[str, float],
    target_id: str,
    confidence: float,
    source: str = "model",
) -> Dict[str, Any]:
    """Build a prediction summary dict compatible with dashboard.js expectations."""
    from backend.app.config.constants import TARGETS
    target = TARGETS.get(target_id.lower())
    sorted_drivers = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    return {
        "target_id": target_id,
        "target_label": target["label"] if target else target_id,
        "predictions": [
            {
                "driver_code": code,
                "probability": round(prob, 6),
                "percentage": round(prob * 100, 2),
            }
            for code, prob in sorted_drivers
        ],
        "confidence": round(confidence, 4),
        "source": source,
        "top_prediction": sorted_drivers[0] if sorted_drivers else None,
        "target_info": target,
    }


def generate_prediction(
    race_id: str,
    session_type: str = "race",
    sub_session: Optional[str] = None,
    weather: str = "dry",
    grid_positions: Optional[Dict[str, int]] = None,
    feature_weights: Optional[Dict[str, float]] = None,
    simulation_count: int = 10000,
    ai_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate comprehensive predictions for any session (race, qualifying, practice)
    supporting all dashboard targets and optional AI blending.
    
    Args:
        race_id: Race identifier
        session_type: Main session type (race, qualifying, practice)
        sub_session: Sub-session type (FP1, FP2, FP3, Q1, Q2, Q3, Race)
        weather: Weather condition (dry, mixed, wet)
        grid_positions: Starting grid positions for race
        feature_weights: Model feature weights
        simulation_count: Number of Monte Carlo simulations
        ai_config: AI configuration for enhancement
    """
    session_type = (session_type or "race").lower()
    sub_session = (sub_session or "").lower()
    weather = (weather or "dry").lower()
    weights = feature_weights or {}
    chaos_level = float(weights.get("chaos_level", 50))
    sim_count = max(100, min(int(simulation_count or 10000), 100_000))

    if not ai_config:
        ai_config = {}
    for key in ["ai_mode", "ai_model", "ai_api_key", "ai_weight", "ai_temperature"]:
        if key in kwargs and key not in ai_config:
            ai_config[key] = kwargs[key]

    ai_mode = ai_config.get("ai_mode", "normal")
    ai_model_name = ai_config.get("ai_model", "gemini-2.0-flash-exp")
    ai_api_key = str(ai_config.get("ai_api_key", "") or "").strip()
    ai_weight = float(ai_config.get("ai_weight", 0.3))
    ai_temp = float(ai_config.get("ai_temperature", 0.7))
    # Only call AI when mode is explicitly 'ai' AND a valid (non-placeholder) key is present
    use_ai = (
        ai_mode == "ai"
        and bool(ai_api_key)
        and not ai_api_key.startswith("YOUR_")
        and len(ai_api_key) > 10
    )

    logger.info(f"Generating prediction: {race_id} / {session_type} / weather={weather} / ai={use_ai}")

    race_info = get_race_by_id(race_id) or {
        "id": race_id,
        "name": race_id.title(),
        "circuit": "Grand Prix Circuit",
        "base_sc": 30,
        "round": 1,
    }
    sc_prob = (race_info.get("base_sc", 30) + (10 if weather != "dry" else 0)) / 100.0

    all_drivers = get_all_drivers()
    all_codes = [d["code"] for d in all_drivers]
    driver_map = {d["code"]: d for d in all_drivers}

    predictions_by_target: Dict[str, Any] = {}
    current_grid: Dict[str, int] = {}
    winner_probabilities: Dict[str, float] = {}

    # =========================================================================
    if session_type == "race":
        # ── 1. Build starting grid ─────────────────────────────────────────────
        mc_instance = MonteCarloSimulator(num_simulations=sim_count)
        if grid_positions and len(grid_positions) > 0:
            current_grid = mc_instance._complete_grid(grid_positions, all_codes)
        else:
            try:
                grid_res = GridModel().get_grid_positions(
                    season=2026, round_number=race_info.get("round", 1)
                )
                candidate = grid_res.get("grid") or {}
                if len(candidate) >= max(1, len(all_codes) // 2):
                    current_grid = mc_instance._complete_grid(candidate, all_codes)
                else:
                    raise ValueError("Incomplete grid")
            except Exception:
                current_grid = _strength_based_grid(all_drivers)

        # ── 2. Monte Carlo simulation ──────────────────────────────────────────
        mc_output = mc_instance.simulate_race(
            race_id=race_id,
            grid_positions=current_grid,
            weather=weather,
            safety_car_prob=sc_prob,
            chaos_level=chaos_level,
            num_simulations=sim_count,
        )

        probs_map = mc_output["results"]["probabilities"]
        conf = float(mc_output["results"]["confidence"])

        # MC probabilities are already normalised — use them directly.
        raw_win    = {c: probs_map[c]["win_prob"]    for c in all_codes}
        raw_podium = {c: probs_map[c]["podium_prob"] for c in all_codes}
        raw_points = {c: probs_map[c]["points_prob"] for c in all_codes}

        # ── 3. Optional AI adjustment (only with a real key) ───────────────────
        ai_source = "model"
        if use_ai:
            try:
                insights_res = ai_client.get_prediction_insights(
                    model=ai_model_name,
                    api_key=ai_api_key,
                    race_context={
                        "race_name": race_info.get("name"),
                        "circuit": race_info.get("circuit"),
                        "weather": weather,
                        "session_type": "race",
                        "sub_session": sub_session or "race",
                    },
                    current_predictions=raw_win,
                    temperature=ai_temp,
                )
                if insights_res and "insights" in insights_res:
                    adjustments = insights_res["insights"].get("adjustments", {})
                    if adjustments:
                        for code, adj in adjustments.items():
                            if code in raw_win:
                                boost = float(adj) * ai_weight
                                raw_win[code]    = max(0.0001, raw_win[code]    + boost)
                                raw_podium[code] = max(0.0001, min(1.0, raw_podium[code] + boost * 2.0))
                                raw_points[code] = max(0.0001, min(1.0, raw_points[code] + boost * 2.5))
                        ai_source = f"model+{ai_model_name}"
            except Exception as ai_err:
                logger.warning(f"AI adjustment skipped: {ai_err}")

        # ── 4. ML ensemble blend (if artifacts available) → Chaos smoothing ──────
        # Try ML zoo — if trained, blend 45% ML / 55% MC; else statistical_fallback
        ml_blend_source = "statistical_fallback"
        blended_win = raw_win
        try:
            from backend.app.config.settings import settings as _s
            if getattr(_s, 'ENABLE_ENSEMBLE', True):
                from backend.app.prediction.orchestrator import _try_ml_predictions, _blend
                ml_probs, src = _try_ml_predictions(all_drivers, race_id, weather, current_grid, session_type, weights)
                if ml_probs is not None:
                    blended_win = _blend(ml_probs, raw_win, weight_ml=0.45)
                    ml_blend_source = src
        except Exception:
            pass
        shaped_win    = _apply_chaos_smoothing(enforce_probability_sum(blended_win),    chaos_level)
        # podium/points remain MC-derived (could add DNF model later)
        shaped_podium = _apply_chaos_smoothing(raw_podium, chaos_level)
        shaped_points = _apply_chaos_smoothing(raw_points, chaos_level)

        eff_source = f"{ai_source}+{ml_blend_source}" if ml_blend_source != "statistical_fallback" else ai_source
        predictions_by_target["winner"] = _build_summary(shaped_win,    "winner", conf, eff_source)
        predictions_by_target["podium"] = _build_summary(shaped_podium, "podium", conf, ai_source)
        predictions_by_target["points"] = _build_summary(shaped_points, "points", conf, ai_source)
        
        # Add sub-session specific race target if specified
        if sub_session:
            predictions_by_target[f"race_{sub_session}"] = _build_summary(shaped_win, f"race_{sub_session}", conf, ai_source)

        winner_probabilities = shaped_win

    # =========================================================================
    elif session_type == "qualifying":
        try:
            grid_res = GridModel().get_grid_positions(
                season=2026, round_number=race_info.get("round", 1)
            )
            current_grid = grid_res.get("grid") or {}
        except Exception:
            current_grid = {}

        if not current_grid:
            current_grid = _strength_based_grid(all_drivers)

        # Different qualifying sessions have different cut-offs and pressure
        session_pressure = 1.0
        if sub_session == "q1":
            session_pressure = 0.9  # Lower pressure, more conservative
        elif sub_session == "q2":
            session_pressure = 1.0  # Medium pressure
        elif sub_session == "q3":
            session_pressure = 1.1  # High pressure for pole position
        
        q3_raw = {}
        for code in all_codes:
            pos = current_grid.get(code, 11)
            d_strength = driver_map[code].get("strength", 50) / 100.0
            wet_skill  = driver_map[code].get("wet_skill", 50) / 100.0
            consistency = driver_map[code].get("consistency", 50) / 100.0
            
            weather_boost = (wet_skill - 0.5) * 0.2 if weather != "dry" else 0.0
            consistency_boost = (consistency - 0.5) * 0.1
            
            base_score = ((23 - pos) / 22.0 * 0.6 + d_strength * 0.4 + weather_boost + consistency_boost) * session_pressure
            q3_raw[code] = max(0.01, base_score)

        shaped_q3 = _apply_chaos_smoothing(enforce_probability_sum(q3_raw), chaos_level)
        conf = probability_model.get_confidence_score(shaped_q3, target_id="q3")
        
        # Main Q3 prediction
        predictions_by_target["q3"] = _build_summary(shaped_q3, "q3", conf, "model")
        
        # Add sub-session specific predictions
        if sub_session:
            sub_key = sub_session.replace(" ", "_")
            predictions_by_target[f"qualifying_{sub_key}"] = _build_summary(
                shaped_q3, f"qualifying_{sub_key}", conf, "model"
            )
        
        winner_probabilities = shaped_q3

    # =========================================================================
    elif session_type == "practice":
        # Different practice sessions have slightly different characteristics
        session_multiplier = 1.0
        if sub_session == "fp1":
            session_multiplier = 0.95  # Drivers still finding setup
        elif sub_session == "fp2":
            session_multiplier = 1.0   # Optimal conditions
        elif sub_session == "fp3":
            session_multiplier = 1.05 # Race setup refinement
        
        pace_raw = {}
        for code in all_codes:
            d_strength = driver_map[code].get("strength", 50) / 100.0
            wet_skill  = driver_map[code].get("wet_skill", 50) / 100.0
            consistency = driver_map[code].get("consistency", 50) / 100.0
            
            # Weather impact varies by session
            weather_boost = (
                (wet_skill - 0.5) * 0.25 if weather == "wet"
                else ((wet_skill - 0.5) * 0.12 if weather == "mixed" else 0.0)
            )
            
            # Consistency matters more in practice
            consistency_factor = (consistency - 0.5) * 0.15
            
            base_pace = d_strength * session_multiplier + weather_boost + consistency_factor
            pace_raw[code] = max(0.01, base_pace)

        shaped_pace = _apply_chaos_smoothing(enforce_probability_sum(pace_raw), chaos_level)
        conf = probability_model.get_confidence_score(shaped_pace, target_id="practice_pace")
        
        # Create practice-specific predictions for different sub-sessions
        predictions_by_target["practice_pace"] = _build_summary(
            shaped_pace, "practice_pace", conf, "model"
        )
        
        # Add sub-session specific target
        if sub_session:
            sub_key = sub_session.replace(" ", "_")
            predictions_by_target[f"practice_{sub_key}"] = _build_summary(
                shaped_pace, f"practice_{sub_key}", conf, "model"
            )
        
        winner_probabilities = shaped_pace
        current_grid = {
            code: i + 1
            for i, code in enumerate(
                sorted(shaped_pace.keys(), key=lambda c: shaped_pace[c], reverse=True)
            )
        }

    # ── Calibrate via fitted calibrator if available ──────────────────────────
    try:
        from backend.app.engine.calibration import probability_calibrator
        if probability_calibrator.is_fitted:
            calibrated_probabilities = probability_calibrator.calibrate_dict(winner_probabilities)
            calibrated_probabilities = enforce_probability_sum(calibrated_probabilities)
        else:
            calibrated_probabilities = calibrate_probabilities(winner_probabilities)
    except Exception:
        calibrated_probabilities = calibrate_probabilities(winner_probabilities)
    confidence_intervals     = calculate_confidence_intervals(calibrated_probabilities)
    model_drift_score        = detect_model_drift(calibrated_probabilities)

    try:
        save_predictions_to_database(race_id, session_type, current_grid, calibrated_probabilities, confidence_intervals)
        save_prediction_metadata(race_id, session_type, calibrated_probabilities, confidence_intervals, model_drift_score)
    except Exception as db_err:
        logger.warning(f"Database save skipped: {db_err}")

    return {
        "race_id": race_id,
        "session_type": session_type,
        "sub_session": sub_session,
        "weather": weather,
        "grid_positions": current_grid,
        "predictions": predictions_by_target,
        "winner_probabilities": calibrated_probabilities,
        "confidence_intervals": confidence_intervals,
        "model_drift_score": model_drift_score,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
    }


def save_predictions_to_database(
    race_id: str,
    session_type: str,
    grid_positions: Dict[str, int],
    winner_probabilities: Dict[str, float],
    confidence_intervals: Dict[str, Dict[str, float]],
) -> bool:
    """Save predictions to database."""
    try:
        db_client = DatabaseClient()
        with db_client.get_session() as db:
            for driver_code in grid_positions:
                probability = winner_probabilities.get(driver_code, 0.0)
                confidence  = confidence_intervals.get(driver_code, {})
                prediction = Prediction(
                    race_id=race_id,
                    session_type=session_type,
                    prediction_type="winner",
                    driver_code=driver_code,
                    probability=probability,
                    confidence_interval=confidence,
                    created_at=datetime.now(),
                )
                db.add(prediction)
            db.commit()
            return True
    except Exception as e:
        logger.error(f"Error saving predictions: {e}")
        return False

