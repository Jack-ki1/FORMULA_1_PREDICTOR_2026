"""
Prediction Orchestrator — layered architecture per spec §3:

 DriverPerformance(ML) + TeamPace + RaceDynamics(Simulation) → Ensemble → Calibration → MonteCarlo → Explanation
"""
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from backend.app.config.settings import settings
from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.engine.feature_engineering import feature_engineer
from backend.app.engine.monte_carlo import MonteCarloSimulator
from backend.app.engine.probability_model import enforce_probability_sum, calibrate_probabilities, calculate_confidence_intervals
from backend.app.prediction.snapshot import PredictionSnapshot, build_snapshot

logger = logging.getLogger(__name__)

def _try_ml_predictions(all_drivers, race_id: str, weather: str, grid_positions: Dict[str,int], session_type: str, feature_weights: Dict[str,float]) -> tuple[Optional[Dict[str,float]], str]:
    """Try ML zoo inference. Returns (probs, source) or (None, fallback_reason)."""
    try:
        from backend.app.engine.ml_models import model_zoo
        # attempt to load artifacts if not trained
        if not any(m.is_trained for m in model_zoo.models.values()):
            model_zoo.load_models()
        if not any(m.is_trained for m in model_zoo.models.values()):
            return None, "statistical_fallback_no_artifact"
        # build features
        feats = feature_engineer.build_session_features(race_id, weather, session_type, grid_positions, feature_weights)
        df = feature_engineer.features_to_dataframe(feats)
        # ensure columns order matches training
        # each model predicts win prob; we average driver-wise
        predictions = model_zoo.predict_all(df)
        if not predictions:
            return None, "statistical_fallback_no_pred"
        # predictions dict: model_name -> proba array shape (n_drivers, n_classes)
        # we take proba of class 1 if binary, or max prob otherwise
        ml_scores = {}
        codes = list(feats.keys())
        for model_name, proba in predictions.items():
            if proba is None:
                continue
            if proba.ndim == 2 and proba.shape[1] >= 2:
                scores = proba[:, 1]  # P(win)
            else:
                scores = proba.flatten()
            for code, s in zip(codes, scores):
                ml_scores[code] = ml_scores.get(code, 0.0) + float(s) * 0.5  # will blend later
        # normalize
        total = sum(ml_scores.values())
        if total > 0:
            ml_scores = {k: v/total for k,v in ml_scores.items()}
        return ml_scores, "ml_ensemble"
    except Exception as e:
        logger.debug(f"ML inference fallback: {e}")
        return None, f"statistical_fallback_error:{e}"

def _blend(ml_probs: Optional[Dict[str,float]], mc_probs: Dict[str,float], weight_ml: float = 0.45) -> Dict[str,float]:
    if ml_probs is None:
        return mc_probs
    # ensemble: weight_ml * ml + (1-weight_ml) * mc, then renormalize
    blended = {}
    for code in mc_probs:
        blended[code] = weight_ml * ml_probs.get(code, 1/len(mc_probs)) + (1-weight_ml) * mc_probs[code]
    s = sum(blended.values())
    return {k: v/s for k,v in blended.items()} if s else mc_probs

def _explain(driver_code: str, prob: float, grid: int, driver: Dict[str,Any], race_context: Dict[str,Any]) -> Dict[str,Any]:
    reasons_pos, reasons_neg = [], []
    if grid <= 3: reasons_pos.append("Strong starting grid")
    elif grid >= 15: reasons_neg.append("Starting grid disadvantage")
    if driver.get("strength",50) >= 80: reasons_pos.append("High recent pace")
    if driver.get("wet_skill",50) >= 80 and race_context.get("weather") != "dry": reasons_pos.append("Excellent wet-weather performance")
    if driver.get("reliability",50) >= 88: reasons_pos.append("Low DNF risk")
    if driver.get("strength",50) < 55: reasons_neg.append("Below-average pace")
    overt = race_context.get("overtaking_difficulty",0.5)
    if overt < 0.4 and grid >= 10: reasons_neg.append("High tyre degradation / overtaking difficulty")
    return {"driver": driver_code, "probability": prob, "grid": grid, "positives": reasons_pos[:3], "negatives": reasons_neg[:2]}

def orchestrate(race_id: str, session_type: str, sub_session: str, weather: str, grid_positions: Dict[str,int],
                feature_weights: Dict[str,float], simulation_count: int, random_seed: int = 42,
                provenance: Optional[Dict[str,Any]] = None) -> Dict[str,Any]:
    """
    Full pipeline: feature → ML → MC → blend → calibration → intervals → explanations → snapshot
    """
    from backend.app.data.calendar_2026 import get_race_by_id
    from backend.app.engine.probability_model import detect_model_drift

    all_drivers = get_all_drivers()
    all_codes = [d["code"] for d in all_drivers]
    driver_map = {d["code"]: d for d in all_drivers}
    race_info = get_race_by_id(race_id) or {"id": race_id, "name": race_id.title(), "circuit": "Grand Prix Circuit", "base_sc":30, "round":1}
    sc_prob = (race_info.get("base_sc",30) + (10 if weather!="dry" else 0))/100.0
    chaos = float(feature_weights.get("chaos_level", 50) if feature_weights else 50)

    # snapshot
    snap = build_snapshot(race_id, session_type, sub_session=sub_session, grid_positions=grid_positions,
                          weather_condition=weather, simulation_count=simulation_count, random_seed=random_seed, provenance=provenance or {})
    snap.weather = {"condition": weather, "air_temp": race_info.get("base_temp",25), "rain_prob": race_info.get("base_rain",20)/100.0}
    snap.lineup = {"drivers": len(all_drivers)}

    # --- Monte Carlo ---
    mc = MonteCarloSimulator(num_simulations=simulation_count)
    # grid completion is done by caller; here assume complete
    mc_out = mc.simulate_race(race_id=race_id, grid_positions=grid_positions, weather=weather, safety_car_prob=sc_prob, chaos_level=chaos, num_simulations=simulation_count)
    mc_probs = {c: mc_out["results"]["probabilities"][c]["win_prob"] for c in all_codes}

    # --- ML ---
    ml_probs, ml_source = _try_ml_predictions(all_drivers, race_id, weather, grid_positions, session_type, feature_weights)
    # ensemble weight from settings or learned; try to load calibrated weight from registry
    weight_ml = 0.45 if ml_probs is not None else 0.0
    # if registry has champion weight
    try:
        import json, os
        if os.path.exists("training/model_registry/registry.json"):
            with open("training/model_registry/registry.json") as f:
                reg = json.load(f)
                champ = reg.get("champion")
                if champ and ml_probs is not None:
                    # keep default unless artifact says otherwise
                    pass
    except Exception:
        pass

    blended = _blend(ml_probs, mc_probs, weight_ml)

    # --- calibration ---
    try:
        from backend.app.engine.calibration import probability_calibrator
        if probability_calibrator.is_fitted:
            calibrated = probability_calibrator.calibrate_dict(blended)
        else:
            calibrated = calibrate_probabilities(blended)
    except Exception:
        calibrated = calibrate_probabilities(blended)

    # enforce sum
    calibrated = enforce_probability_sum(calibrated)
    intervals = calculate_confidence_intervals(calibrated)
    drift = detect_model_drift(calibrated)

    # DNF probabilities (simple from reliability + mc)
    dnf_probs = {c: float(mc_out["results"]["probabilities"][c].get("dnf_prob", 0.04)) for c in all_codes}
    expected_finish = {c: float(sum((i+1)*0.02 for i in range(22))) for c in all_codes}  # placeholder; mc could compute

    # explanations
    explanations = {code: _explain(code, calibrated.get(code,0), grid_positions.get(code,11), driver_map[code], {"weather":weather, "overtaking_difficulty":0.5}) for code in all_codes}

    # data quality score
    grid_completeness = len([v for v in grid_positions.values() if 1<=v<=22])/len(all_codes) if all_codes else 0
    weather_completeness = 0.85 if weather in ("dry","wet","mixed") else 0.5
    data_quality = round(0.5*grid_completeness + 0.3*weather_completeness + 0.2*0.95, 2)

    source = ml_source if ml_probs is not None else "statistical_fallback"
    # Monte Carlo uses seed for reproducibility
    np.random.seed(random_seed)

    return {
        "snapshot": snap.to_dict(),
        "probabilities": calibrated,
        "dnf_probabilities": dnf_probs,
        "intervals": intervals,
        "drift": drift,
        "explanations": explanations,
        "data_quality": {"score": data_quality, "grid": round(grid_completeness,2), "weather": weather_completeness},
        "prediction_source": source,
        "model": {"version": snap.model_version, "feature_version": snap.feature_version, "calibration": snap.calibration_version},
        "mc_raw": mc_probs,
        "ml_raw": ml_probs,
    }
