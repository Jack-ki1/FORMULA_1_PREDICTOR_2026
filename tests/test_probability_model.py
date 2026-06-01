"""
Comprehensive tests for the probability model and simulation engine.

Tests cover:
- Driver presence and completeness
- Probability normalization (win probs sum to 1)
- Probability hierarchy (win <= top3 <= top10)
- Position counts + DNFs = total simulations
- Safety car impact on win distribution
- Reproducibility with seeds
"""

import pytest
from engine.probability_model import simulate_race, predict_race


class TestSimulateRace:
    """Core simulation engine tests."""
    
    @pytest.fixture(scope="class")
    def canada_sim(self):
        """Run a single simulation for Canada circuit."""
        return simulate_race("canada", n_runs=2000, seed=42)
    
    @pytest.fixture(scope="class")
    def monza_sim(self):
        """Run a single simulation for Monza circuit."""
        return simulate_race("italy", n_runs=2000, seed=42)
    
    def test_all_drivers_present(self, canada_sim):
        """All active drivers should be present in simulation results."""
        from data.driver_data import get_all_drivers
        expected_ids = {d["id"] for d in get_all_drivers() if d.get("active", True)}
        actual_ids = set(canada_sim["stats"].keys())
        
        missing = expected_ids - actual_ids
        extra = actual_ids - expected_ids
        
        assert not missing, f"Missing drivers from results: {missing}"
        assert not extra, f"Unexpected drivers in results: {extra}"
    
    def test_win_probabilities_sum_to_one(self, canada_sim):
        """Win probabilities across all drivers should sum to approximately 1.0."""
        total = sum(v["win_probability"] for v in canada_sim["stats"].values())
        assert abs(total - 1.0) < 0.02, f"Win probs sum to {total:.4f}, expected ~1.0"
    
    def test_probability_hierarchy_per_driver(self, canada_sim):
        """For each driver: win_prob <= top3_prob <= top10_prob."""
        for did, stats in canada_sim["stats"].items():
            assert stats["win_probability"] <= stats["top3_probability"] + 1e-6, \
                f"{did}: win ({stats['win_probability']}) > top3 ({stats['top3_probability']})"
            assert stats["top3_probability"] <= stats["top10_probability"] + 1e-6, \
                f"{did}: top3 ({stats['top3_probability']}) > top10 ({stats['top10_probability']})"
    
    def test_position_counts_plus_dnfs_equal_runs(self, canada_sim):
        """Position counts + DNFs should equal total simulation runs."""
        N = 2000
        for did, stats in canada_sim["stats"].items():
            pos_total = sum(stats["position_distribution"])
            dnf_count = stats["dnf_count"]
            assert abs(pos_total + dnf_count - N) <= 2, (
                f"{did}: {pos_total} finishes + {dnf_count} DNFs ≠ {N} simulations"
            )
    
    def test_sc_boost_does_not_help_front_runners(self, canada_sim, monza_sim):
        """
        Safety car circuit should compress win distributions vs no-SC circuit.
        
        Canada has high SC probability (0.45), Monza has low SC probability (0.25).
        The max single-driver win probability should be lower at high-SC circuits
        because SC events introduce more randomness and help mid-field drivers.
        """
        canada_max_win = max(v["win_probability"] for v in canada_sim["stats"].values())
        monza_max_win = max(v["win_probability"] for v in monza_sim["stats"].values())
        
        # High-SC circuit should produce more compressed win distribution
        assert canada_max_win <= monza_max_win + 0.05, (
            f"Canada max win {canada_max_win:.3f} should not significantly exceed "
            f"Monza {monza_max_win:.3f} (high-SC circuits compress win distribution)"
        )
    
    def test_reproducibility_with_seed(self):
        """Same seed should produce identical results."""
        sim1 = simulate_race("canada", n_runs=1000, seed=123)
        sim2 = simulate_race("canada", n_runs=1000, seed=123)
        
        # Check win probabilities match exactly
        for did in sim1["stats"]:
            assert sim1["stats"][did]["win_probability"] == sim2["stats"][did]["win_probability"], \
                f"Non-reproducible result for {did}"
    
    def test_dnf_probabilities_in_valid_range(self, canada_sim):
        """DNF probabilities should be between 0 and 0.45."""
        for did, stats in canada_sim["stats"].items():
            dnf_prob = stats["dnf_probability"]
            assert 0.0 <= dnf_prob <= 0.45, \
                f"{did} DNF probability {dnf_prob} out of range [0, 0.45]"
    
    def test_expected_positions_in_valid_range(self, canada_sim):
        """Expected positions should be between 1 and field size."""
        field_size = len(canada_sim["stats"])
        for did, stats in canada_sim["stats"].items():
            exp_pos = stats["expected_position"]
            assert 1.0 <= exp_pos <= field_size, \
                f"{did} expected position {exp_pos} out of range [1, {field_size}]"


class TestPredictRace:
    """Integration tests for the predict_race wrapper."""
    
    def test_predict_race_returns_all_required_fields(self):
        """predict_race should return all required fields."""
        result = predict_race("canada", n_simulations=500, seed=42)
        
        required_fields = ["stats", "confidence_intervals"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
    
    def test_predict_race_all_drivers_have_predictions(self):
        """All active drivers should have predictions."""
        from data.driver_data import get_all_drivers
        
        result = predict_race("canada", n_simulations=500, seed=42)
        expected_ids = {d["id"] for d in get_all_drivers() if d.get("active", True)}
        actual_ids = set(result["stats"].keys())
        
        assert expected_ids == actual_ids, \
            f"Driver mismatch: missing={expected_ids - actual_ids}, extra={actual_ids - expected_ids}"
    
    def test_predict_race_confidence_intervals_present(self):
        """Confidence intervals should be present for all drivers."""
        result = predict_race("canada", n_simulations=500, seed=42)
        
        for did in result["stats"]:
            assert did in result["confidence_intervals"], \
                f"Missing confidence interval for {did}"
            
            ci = result["confidence_intervals"][did]
            required_ci = ["win_ci", "top3_ci", "top10_ci", "dnf_ci"]
            for ci_type in required_ci:
                assert ci_type in ci, f"Missing {ci_type} confidence interval for {did}"


class TestSafetyCarVectorized:
    """Tests specifically for the vectorized SC boost fix."""
    
    def test_vectorized_sc_per_simulation(self):
        """
        Vectorized simulation should apply SC independently per simulation.
        
        With 10,000 sims and SC probability 0.45, we expect ~4,500 sims with SC.
        The boost should not be applied uniformly to all sims.
        """
        from engine.vectorized_simulation import simulate_race_vectorized
        from data.circuit_data import get_circuit
        
        # Canada has high SC probability
        circuit = get_circuit("canada")
        sc_prob = circuit.get("safety_car_probability", 0.5)
        
        result = simulate_race_vectorized("canada", n_runs=10000, seed=42)
        
        # Win probabilities should be more distributed than a no-SC scenario
        # This is a sanity check that SC boost is working
        max_win_prob = max(v["win_probability"] for v in result["stats"].values())
        
        # With high SC probability, max win prob should be below 50%
        assert max_win_prob < 0.50, (
            f"Max win probability {max_win_prob:.3f} too high for high-SC circuit "
            f"(suggests SC boost may not be applied per-simulation)"
        )
