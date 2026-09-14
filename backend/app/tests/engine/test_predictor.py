"""
Tests for predictor orchestrator and multi-target session predictions.
"""
import pytest
from backend.app.engine.predictor import generate_prediction


def test_generate_prediction_race():
    """Test race prediction returns winner, podium, points targets and grid."""
    result = generate_prediction("bahrain", "race", weather="dry", simulation_count=1000)
    assert result["status"] == "success"
    assert result["race_id"] == "bahrain"
    assert result["session_type"] == "race"
    assert "grid_positions" in result
    assert len(result["grid_positions"]) == 22
    assert "predictions" in result

    preds = result["predictions"]
    assert "winner" in preds
    assert "podium" in preds
    assert "points" in preds

    winner_preds = preds["winner"]["predictions"]
    assert len(winner_preds) == 22
    # Winner probabilities should sum to approximately 1.0
    total_win_prob = sum(p["probability"] for p in winner_preds)
    assert abs(total_win_prob - 1.0) < 0.05


def test_generate_prediction_qualifying():
    """Test qualifying prediction returns q3 target and grid positions."""
    result = generate_prediction("bahrain", "qualifying", weather="dry")
    assert result["status"] == "success"
    assert result["session_type"] == "qualifying"
    assert "predictions" in result
    assert "q3" in result["predictions"]
    assert len(result["predictions"]["q3"]["predictions"]) == 22
    assert "grid_positions" in result


def test_generate_prediction_practice():
    """Test practice prediction returns practice_pace target."""
    result = generate_prediction("bahrain", "practice", weather="dry")
    assert result["status"] == "success"
    assert result["session_type"] == "practice"
    assert "predictions" in result
    assert "practice_pace" in result["predictions"]


def test_generate_prediction_with_manual_grid():
    """Test race prediction respects user-supplied manual grid positions."""
    manual_grid = {"VER": 1, "HAM": 2, "NOR": 3}
    result = generate_prediction("bahrain", "race", grid_positions=manual_grid, simulation_count=500)
    assert result["grid_positions"]["VER"] == 1
    assert result["grid_positions"]["HAM"] == 2
    assert result["grid_positions"]["NOR"] == 3
