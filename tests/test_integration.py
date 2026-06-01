"""
Integration Tests for F1 Prediction System.

Tests the full prediction pipeline and data consistency.
"""

import pytest


def test_full_prediction_pipeline():
    """Test end-to-end prediction with monotonicity constraints."""
    from engine.predictor import predict, PredictionRequest
    
    result = predict(PredictionRequest(circuit_id="canada", n_simulations=500))
    
    assert "predictions" in result
    assert len(result["predictions"]) > 0
    
    for pred in result["predictions"]:
        assert 0 <= pred["win_pct"] <= 100
        assert 0 <= pred["top3_pct"] <= 100
        assert pred["win_pct"] <= pred["top3_pct"], f"Win ({pred['win_pct']}) > Top3 ({pred['top3_pct']})"
        assert pred["top3_pct"] <= pred["top10_pct"], f"Top3 ({pred['top3_pct']}) > Top10 ({pred['top10_pct']})"
    
    # Win probs should sum to approximately 100%
    total_win_pct = sum(p["win_pct"] for p in result["predictions"])
    assert 95 <= total_win_pct <= 105, f"Win probabilities sum to {total_win_pct}, expected ~100"


def test_feature_weight_keys_match_engine():
    """Verify FEATURE_WEIGHTS keys match actual engine feature keys."""
    from config.settings import FEATURE_WEIGHTS
    from engine.feature_engineering import compute_composite_score
    
    result = compute_composite_score("antonelli", "canada")
    engine_keys = set(result["features"].keys())
    weight_keys = set(FEATURE_WEIGHTS.keys())
    
    assert engine_keys == weight_keys, \
        f"Key mismatch:\nEngine: {engine_keys}\nWeights: {weight_keys}"


def test_no_duplicate_drivers():
    """Ensure no duplicate driver IDs."""
    from data.driver_data import get_all_drivers
    
    ids = [d["id"] for d in get_all_drivers()]
    duplicates = [x for x in ids if ids.count(x) > 1]
    assert len(duplicates) == 0, f"Duplicate driver IDs: {set(duplicates)}"


def test_driver_teams_consistent_with_constructor_mapping():
    """Verify Hamilton team consistency across files."""
    from data.driver_data import DRIVERS
    from data.season_2026 import CONSTRUCTOR_MAPPING
    
    for driver_id, mapping_team in CONSTRUCTOR_MAPPING.items():
        if driver_id in DRIVERS:
            driver_team = DRIVERS[driver_id]["team"]
            assert driver_team == mapping_team, \
                f"{driver_id}: driver_data says {driver_team}, CONSTRUCTOR_MAPPING says {mapping_team}"


def test_api_routes_import():
    """Test that routes import without logger errors."""
    from api.routes import router, logger
    assert logger is not None
    assert router is not None


def test_data_quality_assertions():
    """Verify round number consistency between calendar and circuit data."""
    from data.calendar_2026 import CALENDAR_2026
    from data.circuit_data import CIRCUITS
    
    cal_rounds = {r["circuit"]: r["round"] for r in CALENDAR_2026}
    mismatches = []
    
    for cid, circuit in CIRCUITS.items():
        if cid in cal_rounds:
            if circuit["round_2026"] != cal_rounds[cid]:
                mismatches.append({
                    "circuit": cid,
                    "calendar_round": cal_rounds[cid],
                    "circuit_round": circuit["round_2026"]
                })
    
    assert len(mismatches) == 0, f"Round mismatches: {mismatches}"


def test_recent_form_score_no_crash():
    """Test Bug 1 fix: compute_recent_form_score handles List[int] correctly."""
    from engine.feature_engineering import compute_recent_form_score
    
    # Should not raise TypeError
    score = compute_recent_form_score("hamilton")
    assert 0.0 <= score <= 1.0
    
    score = compute_recent_form_score("antonelli")
    assert 0.0 <= score <= 1.0


def test_hamilton_team_consistency():
    """Test Conflict 1 fix: Hamilton team is consistent."""
    from data.driver_data import DRIVERS
    from data.season_2026 import CONSTRUCTOR_MAPPING
    
    assert DRIVERS["hamilton"]["team"] == CONSTRUCTOR_MAPPING["hamilton"]
    assert DRIVERS["hamilton"]["team"] == "mercedes"


def test_constructor_strength_values_reasonable():
    """Test Conflict 2 fix: Red Bull strength is reasonable."""
    from engine.feature_engineering import _CONSTRUCTOR_STRENGTH
    
    red_bull_strength = _CONSTRUCTOR_STRENGTH.get("red_bull", 0)
    assert red_bull_strength >= 0.80, f"Red Bull strength too low: {red_bull_strength}"
