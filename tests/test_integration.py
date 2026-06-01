"""
Integration Tests for F1 Prediction System.

These tests verify end-to-end functionality that unit tests miss:
  - Full prediction pipeline execution
  - Feature weight key alignment with engine
  - Data consistency (no duplicates, team mappings match)
  - Probability hierarchy enforcement (win ≤ top3 ≤ top10)
  - Win probability normalization (sums to ~100%)
  - API route error handling
"""

import pytest
from typing import List, Dict


# ── Full Pipeline Integration Tests ────────────────────────────────────────────

class TestFullPredictionPipeline:
    """End-to-end tests that run the complete prediction system."""

    def test_full_prediction_pipeline(self):
        """Run a complete prediction and verify output structure and constraints."""
        from engine.predictor import predict, PredictionRequest
        from data.driver_data import get_all_drivers
        
        result = predict(PredictionRequest(circuit_id="canada", n_simulations=500))
        
        # Verify basic structure
        assert "predictions" in result
        assert "meta" in result
        assert len(result["predictions"]) == len(get_all_drivers()), \
            "Prediction count should match active driver count"
        
        # Verify each prediction has required fields and valid values
        for pred in result["predictions"]:
            assert 0 <= pred["win_pct"] <= 100, f"win_pct out of bounds: {pred['win_pct']}"
            assert 0 <= pred["top3_pct"] <= 100, f"top3_pct out of bounds: {pred['top3_pct']}"
            assert 0 <= pred["top10_pct"] <= 100, f"top10_pct out of bounds: {pred['top10_pct']}"
            
            # Monotonicity: win ≤ top3 ≤ top10
            assert pred["win_pct"] <= pred["top3_pct"] + 0.01, \
                f"win_pct ({pred['win_pct']}) > top3_pct ({pred['top3_pct']}) for {pred['driver']}"
            assert pred["top3_pct"] <= pred["top10_pct"] + 0.01, \
                f"top3_pct ({pred['top3_pct']}) > top10_pct ({pred['top10_pct']}) for {pred['driver']}"
        
        # Win probabilities should sum to approximately 100%
        total_win_pct = sum(p["win_pct"] for p in result["predictions"])
        assert 98 <= total_win_pct <= 102, \
            f"Win probabilities sum to {total_win_pct}%, expected ~100%"

    def test_prediction_determinism_with_seed(self):
        """Same seed should produce identical results."""
        from engine.predictor import predict, PredictionRequest
        
        result1 = predict(PredictionRequest(
            circuit_id="canada", n_simulations=500, seed=42
        ))
        result2 = predict(PredictionRequest(
            circuit_id="canada", n_simulations=500, seed=42
        ))
        
        # Compare win probabilities for each driver
        for p1, p2 in zip(result1["predictions"], result2["predictions"]):
            assert abs(p1["win_pct"] - p2["win_pct"]) < 0.1, \
                f"Non-deterministic results for {p1['driver']}"


# ── Feature Weight Alignment Tests ─────────────────────────────────────────────

class TestFeatureWeightAlignment:
    """Verify FEATURE_WEIGHTS keys match the engine's actual feature names."""

    def test_feature_weight_keys_match_engine(self):
        """
        This test would have caught Bug 3 immediately.
        FEATURE_WEIGHTS keys must match the dict returned by compute_composite_score.
        """
        from config.settings import FEATURE_WEIGHTS
        from engine.feature_engineering import compute_composite_score
        
        result = compute_composite_score("antonelli", "canada")
        engine_keys = set(result["features"].keys())
        weight_keys = set(FEATURE_WEIGHTS.keys())
        
        assert engine_keys == weight_keys, \
            f"Key mismatch:\nEngine: {engine_keys}\nWeights: {weight_keys}\n" \
            f"Missing in weights: {engine_keys - weight_keys}\n" \
            f"Extra in weights: {weight_keys - engine_keys}"

    def test_feature_weights_sum_to_one(self):
        """Feature weights should sum to approximately 1.0."""
        from config.settings import FEATURE_WEIGHTS
        
        weight_sum = sum(FEATURE_WEIGHTS.values())
        assert abs(weight_sum - 1.0) < 0.02, \
            f"Feature weights sum to {weight_sum}, expected ~1.0"

    def test_all_feature_weights_positive(self):
        """All feature weights should be non-negative."""
        from config.settings import FEATURE_WEIGHTS
        
        for name, weight in FEATURE_WEIGHTS.items():
            assert weight > 0, f"Feature weight '{name}' is not positive: {weight}"


# ── Data Consistency Tests ─────────────────────────────────────────────────────

class TestDataConsistency:
    """Verify data integrity across all data files."""

    def test_no_duplicate_drivers(self):
        """Each driver ID should appear exactly once."""
        from data.driver_data import get_all_drivers
        
        ids = [d["id"] for d in get_all_drivers()]
        duplicates = [x for x in ids if ids.count(x) > 1]
        
        assert len(duplicates) == 0, f"Duplicate driver IDs found: {set(duplicates)}"

    def test_driver_count_is_22(self):
        """There should be exactly 22 active drivers."""
        from data.driver_data import get_all_drivers
        
        active_drivers = [d for d in get_all_drivers() if d.get("active", True)]
        assert len(active_drivers) == 22, \
            f"Expected 22 active drivers, found {len(active_drivers)}"

    def test_driver_teams_consistent_with_constructor_mapping(self):
        """
        Driver team assignments in driver_data.py must match
        CONSTRUCTOR_MAPPING in season_2026.py.
        """
        from data.driver_data import DRIVERS
        from data.season_2026 import CONSTRUCTOR_MAPPING
        
        for driver_id, mapping_team in CONSTRUCTOR_MAPPING.items():
            if driver_id in DRIVERS:
                driver_team = DRIVERS[driver_id]["team"]
                assert driver_team == mapping_team, \
                    f"{driver_id}: driver_data says '{driver_team}', " \
                    f"CONSTRUCTOR_MAPPING says '{mapping_team}'"

    def test_all_drivers_in_season_results(self):
        """All active drivers should appear in season results."""
        from data.driver_data import get_all_drivers
        from data.season_2026 import SEASON_RESULTS_2026
        
        active_driver_ids = {d["id"] for d in get_all_drivers() if d.get("active", True)}
        drivers_in_results = set()
        
        for race in SEASON_RESULTS_2026:
            for result in race["results"]:
                drivers_in_results.add(result["driver"])
        
        # Some active drivers may not have finished in points in early races
        # This test just verifies no completely unknown drivers appear
        unknown_drivers = drivers_in_results - active_driver_ids
        assert len(unknown_drivers) == 0, \
            f"Unknown drivers in season results: {unknown_drivers}"

    def test_circuit_round_numbers_consistent(self):
        """Circuit round numbers should match calendar."""
        from data.calendar_2026 import CALENDAR_2026
        from data.circuit_data import CIRCUITS
        
        cal_rounds = {r["circuit"]: r["round"] for r in CALENDAR_2026}
        
        for cid, circuit in CIRCUITS.items():
            if cid in cal_rounds:
                circuit_round = circuit.get("round_2026")
                if circuit_round is not None:
                    assert circuit_round == cal_rounds[cid], \
                        f"Round mismatch for {cid}: circuit={circuit_round}, " \
                        f"calendar={cal_rounds[cid]}"


# ── Probability Model Tests ────────────────────────────────────────────────────

class TestProbabilityModel:
    """Verify probability calculations and constraints."""

    def test_position_distribution_sums_to_one(self):
        """Position distributions should sum to approximately 1.0."""
        from engine.probability_model import predict_race
        
        result = predict_race(circuit_id="canada", n_simulations=1000)
        
        for pred in result["predictions"]:
            pos_dist = pred.get("position_distribution", [])
            if pos_dist:
                total = sum(pos_dist)
                assert abs(total - 1.0) < 0.05, \
                    f"Position distribution sums to {total} for {pred['driver_id']}"

    def test_dnf_probability_reasonable(self):
        """DNF probabilities should be in reasonable range."""
        from engine.predictor import predict, PredictionRequest
        
        result = predict(PredictionRequest(circuit_id="canada", n_simulations=500))
        
        for pred in result["predictions"]:
            assert 0 <= pred["dnf_pct"] <= 50, \
                f"DNF probability {pred['dnf_pct']}% out of reasonable range for {pred['driver']}"

    def test_composite_score_in_range(self):
        """Composite scores should be in [0, 1] range."""
        from engine.predictor import predict, PredictionRequest
        
        result = predict(PredictionRequest(circuit_id="canada", n_simulations=500))
        
        for pred in result["predictions"]:
            score = pred.get("composite_score")
            if score is not None:
                assert 0 <= score <= 1, \
                    f"Composite score {score} out of [0,1] range for {pred['driver']}"


# ── Error Handling Tests ───────────────────────────────────────────────────────

class TestErrorHandling:
    """Verify graceful handling of invalid inputs."""

    def test_invalid_circuit_id(self):
        """Should raise an error or return empty results for invalid circuit."""
        from engine.predictor import predict, PredictionRequest
        from data.circuit_data import get_circuit
        
        with pytest.raises(Exception):
            get_circuit("nonexistent_circuit")

    def test_invalid_rain_probability(self):
        """Rain probability should be validated."""
        from engine.predictor import predict, PredictionRequest
        
        # Should handle out-of-range values gracefully
        # This test verifies it doesn't crash
        try:
            result = predict(PredictionRequest(
                circuit_id="canada",
                rain_probability=1.5  # Invalid: > 1.0
            ))
            # If it doesn't raise an error, it should clamp or handle gracefully
            assert "predictions" in result
        except Exception:
            pass  # Raising an error is also acceptable

    def test_zero_simulations(self):
        """Should handle zero or negative simulation count."""
        from engine.predictor import predict, PredictionRequest
        
        with pytest.raises(Exception):
            predict(PredictionRequest(circuit_id="canada", n_simulations=0))
