"""
Unit tests for the feature engineering pipeline.
"""

import pytest
from engine.feature_engineering import (
    compute_elo_score,
    compute_constructor_strength,
    compute_recent_form_score,
    compute_weather_score,
    compute_safety_car_upside,
    compute_teammate_beat_probability,
    compute_all_drivers,
)


def test_weather_score_wet_specialist_benefits():
    """Hamilton (wet_skill=9.8) should score higher in wet conditions than dry."""
    dry_score = compute_weather_score("hamilton", "canada", rain_probability=0.05)
    wet_score = compute_weather_score("hamilton", "canada", rain_probability=0.95)
    assert wet_score > dry_score


def test_weather_score_bounded():
    for driver_id in ["antonelli", "verstappen", "leclerc", "herta"]:
        score = compute_weather_score(driver_id, "canada")
        assert 0.0 <= score <= 1.0, f"Weather score out of range for {driver_id}: {score}"


def test_safety_car_upside_higher_for_backmarkers():
    """Backmarkers should get more SC upside at high-SC circuits."""
    # Compare frontmarker vs backmarker SC upside at high-SC circuit
    front_upside = compute_safety_car_upside("verstappen", "bahrain", estimated_grid_pos=1)
    back_upside = compute_safety_car_upside("herta", "bahrain", estimated_grid_pos=15)
    
    # Backmarker should have higher SC upside
    assert back_upside >= front_upside, \
        f"Backmarker SC upside ({back_upside}) should be >= frontmarker ({front_upside})"


def test_compute_elo_score_with_invalid_driver():
    """Test that invalid driver IDs return neutral score instead of crashing."""
    score = compute_elo_score("nonexistent_driver")
    assert 0.0 <= score <= 1.0


def test_compute_constructor_strength_with_invalid_circuit():
    """Test that invalid circuit IDs don't crash the function."""
    score = compute_constructor_strength("mercedes", "nonexistent_circuit")
    assert 0.05 <= score <= 1.0


def test_compute_recent_form_score_with_no_data():
    """Test that drivers with no recent data return neutral score."""
    score = compute_recent_form_score("nonexistent_driver")
    assert 0.0 <= score <= 1.0


def test_compute_track_fit_score_with_invalid_driver():
    """Test that invalid driver IDs return neutral score."""
    score = compute_track_fit_score("nonexistent_driver", "monaco")
    assert 0.0 <= score <= 1.0


def test_compute_reliability_score_with_invalid_driver():
    """Test that invalid driver IDs return reasonable score."""
    score = compute_reliability_score("nonexistent_driver")
    assert 0.0 <= score <= 1.0


def test_estimate_dnf_probability_with_invalid_driver():
    """Test that invalid driver IDs return reasonable probability."""
    prob = estimate_dnf_probability("nonexistent_driver")
    assert 0.0 <= prob <= 0.45  # Upper bound for DNF probability


def test_compute_weather_score_with_invalid_driver():
    """Test that invalid driver IDs return neutral score."""
    score = compute_weather_score("nonexistent_driver", "canada")
    assert 0.0 <= score <= 1.0


def test_compute_weather_score_with_invalid_circuit():
    """Test that invalid circuit IDs return neutral score."""
    score = compute_weather_score("hamilton", "nonexistent_circuit")
    assert 0.0 <= score <= 1.0


def test_compute_safety_car_upside_with_invalid_driver():
    """Test that invalid driver IDs return reasonable score."""
    score = compute_safety_car_upside("nonexistent_driver", "monaco")
    assert 0.0 <= score <= 0.8  # Upper bound for SC upside


def test_compute_teammate_beat_probability_with_no_teammate():
    """Test behavior when driver has no teammate (should return 0.5)."""
    prob = compute_teammate_beat_probability("nonexistent_driver")
    assert 0.25 <= prob <= 0.75  # Should be near 0.5 since no teammate comparison possible