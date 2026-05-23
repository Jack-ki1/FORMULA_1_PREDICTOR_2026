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
    compute_track_fit_score,
    compute_reliability_score,
    estimate_dnf_probability,
    compute_composite_score,
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
    assert back_upside >= front_upside, (
        f"Backmarker SC upside ({back_upside}) should be >= frontmarker ({front_upside})"
    )


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


def test_compute_composite_score_feature_keys_and_bounds():
    result = compute_composite_score("antonelli", "canada")
    features = result["features"]

    expected_keys = [
        "elo_rating",
        "constructor_strength",
        "recent_form",
        "track_type_fit",
        "reliability",
        "weather_adjustment",
        "safety_car_upside",
        "grid_position",
    ]
    assert list(features.keys()) == expected_keys

    for k, v in features.items():
        assert isinstance(v, (float, int)), f"{k} should be numeric"
        assert 0.0 <= float(v) <= 1.0, f"{k} out of bounds: {v}"

    assert 0.0 <= result["composite_score"] <= 1.0


def test_weather_score_increases_with_rain_for_known_wet_specialist():
    dry_score = compute_weather_score("hamilton", "canada", rain_probability=0.05)
    mid_score = compute_weather_score("hamilton", "canada", rain_probability=0.50)
    wet_score = compute_weather_score("hamilton", "canada", rain_probability=0.95)

    assert wet_score >= mid_score >= dry_score


def test_safety_car_upside_monotonic_with_grid_proxy_on_high_sc_circuit():
    """For a fixed circuit, increasing estimated_grid_pos (worse grid) should not reduce SC upside."""
    circuit_id = "bahrain"
    driver_id = "verstappen"

    ups = [
        compute_safety_car_upside(driver_id, circuit_id, estimated_grid_pos=g)
        for g in [1, 5, 10, 15, 20]
    ]

    assert ups == sorted(ups), f"Expected monotonic SC upside, got: {ups}"


def test_compute_all_drivers_deterministic_ordering_for_fixed_rain_probability():
    r1 = compute_all_drivers("canada", rain_probability=0.33)
    r2 = compute_all_drivers("canada", rain_probability=0.33)

    assert [p["driver_id"] for p in r1] == [p["driver_id"] for p in r2]
    assert [p["composite_score"] for p in r1] == [p["composite_score"] for p in r2]


def test_teammate_beat_probability_bounds_for_known_drivers():
    """Teammate beat probability should always be clamped into [0.05, 0.95]."""
    for driver_id in ["hamilton", "verstappen", "leclerc"]:
        prob = compute_teammate_beat_probability(driver_id)
        assert 0.05 <= prob <= 0.95


