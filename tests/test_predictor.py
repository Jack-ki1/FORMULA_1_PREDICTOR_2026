"""
Tests for the prediction engine.
Runs fast (low simulations) — intended for CI.
"""

import pytest
from engine.predictor import predict, PredictionRequest
from engine.feature_engineering import (
    compute_elo_score,
    compute_constructor_strength,
    compute_recent_form_score,
    compute_track_fit_score,
    compute_reliability_score,
    estimate_dnf_probability,
    compute_composite_score,
    compute_all_drivers,
)
from data.driver_data import get_driver, get_all_drivers
from data.circuit_data import get_circuit


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def canada_prediction():
    return predict(PredictionRequest(circuit_id="canada", n_simulations=200))


@pytest.fixture
def canada_prediction_wet():
    return predict(PredictionRequest(circuit_id="canada", rain_probability=0.90, n_simulations=200))


# ── Data integrity ─────────────────────────────────────────────────────────────

class TestDataIntegrity:
    def test_all_drivers_have_required_fields(self):
        required = ["id", "name", "team", "elo", "dnf_rate_recent", "track_type_fit", "recent_form"]
        for d in get_all_drivers():
            for field in required:
                assert field in d, f"Driver {d['id']} missing field '{field}'"

    def test_elo_in_reasonable_range(self):
        for d in get_all_drivers():
            assert 1400 <= d["elo"] <= 1700, f"ELO out of range for {d['id']}: {d['elo']}"

    def test_dnf_rates_bounded(self):
        for d in get_all_drivers():
            assert 0.0 <= d["dnf_rate_recent"] <= 1.0
            assert 0.0 <= d["dnf_rate_career"] <= 1.0

    def test_circuit_canada_exists(self):
        c = get_circuit("canada")
        assert c["safety_car_probability"] > 0
        assert c["lap_count"] > 0

    def test_circuit_sc_probability_bounded(self):
        c = get_circuit("canada")
        assert 0.0 <= c["safety_car_probability"] <= 1.0


# ── Feature engineering ────────────────────────────────────────────────────────

class TestFeatureEngineering:
    def test_elo_score_bounded(self):
        score = compute_elo_score("antonelli")
        assert 0.0 <= score <= 1.0

    def test_elo_leader_higher_than_backmarker(self):
        leader_score = compute_elo_score("antonelli")
        back_score = compute_elo_score("herta")
        assert leader_score > back_score

    def test_constructor_strength_mercedes_highest(self):
        merc = compute_constructor_strength("mercedes", "canada")
        aston = compute_constructor_strength("aston_martin", "canada")
        assert merc > aston

    def test_constructor_strength_bounded(self):
        for team in ["mercedes", "ferrari", "mclaren", "red_bull", "haas"]:
            s = compute_constructor_strength(team, "canada")
            assert 0.0 <= s <= 1.0, f"Constructor strength out of range for {team}: {s}"

    def test_recent_form_score_bounded(self):
        for d in get_all_drivers()[:5]:
            score = compute_recent_form_score(d["id"])
            assert 0.0 <= score <= 1.0

    def test_dnf_probability_bounded(self):
        for d in get_all_drivers():
            dnf = estimate_dnf_probability(d["id"])
            assert 0.0 <= dnf <= 0.5, f"DNF prob out of range for {d['id']}: {dnf}"

    def test_composite_score_bounded(self):
        result = compute_composite_score("antonelli", "canada")
        assert 0.0 <= result["composite_score"] <= 1.0

    def test_composite_score_has_all_features(self):
        result = compute_composite_score("antonelli", "canada")
        expected_keys = ["elo_rating", "constructor_strength", "recent_form", "track_type_fit"]
        for k in expected_keys:
            assert k in result["features"]

    def test_all_drivers_compute_without_error(self):
        results = compute_all_drivers("canada")
        assert len(results) == len(get_all_drivers())


# ── Probability model ──────────────────────────────────────────────────────────

class TestProbabilityModel:
    def test_win_probs_sum_to_one(self, canada_prediction):
        total = sum(p["win_pct"] for p in canada_prediction["predictions"])
        assert abs(total - 100.0) < 2.0, f"Win probs sum to {total}, expected ~100"

    def test_all_probabilities_bounded(self, canada_prediction):
        for p in canada_prediction["predictions"]:
            assert 0 <= p["win_pct"] <= 100
            assert 0 <= p["top3_pct"] <= 100
            assert 0 <= p["top10_pct"] <= 100
            assert 0 <= p["dnf_pct"] <= 100

    def test_top3_gte_win(self, canada_prediction):
        for p in canada_prediction["predictions"]:
            assert p["top3_pct"] >= p["win_pct"], (
                f"{p['driver']}: top3 ({p['top3_pct']}) < win ({p['win_pct']})"
            )

    def test_top10_gte_top3(self, canada_prediction):
        for p in canada_prediction["predictions"]:
            assert p["top10_pct"] >= p["top3_pct"], (
                f"{p['driver']}: top10 ({p['top10_pct']}) < top3 ({p['top3_pct']})"
            )

    def test_antonelli_highest_win_prob(self, canada_prediction):
        win_probs = {p["driver"]: p["win_pct"] for p in canada_prediction["predictions"]}
        assert win_probs.get("Kimi Antonelli", 0) == max(win_probs.values()), (
            "Antonelli should have highest win probability given 2026 form"
        )

    def test_mercedes_drivers_in_top5(self, canada_prediction):
        top5 = [p["driver"] for p in canada_prediction["predictions"][:5]]
        assert any("Antonelli" in d or "Russell" in d for d in top5), (
            "At least one Mercedes driver should be in predicted top 5"
        )

    def test_correct_driver_count(self, canada_prediction):
        assert len(canada_prediction["predictions"]) == len(get_all_drivers())

    def test_wet_scenario_boosts_hamilton(self, canada_prediction, canada_prediction_wet):
        def get_win(pred, name):
            for p in pred["predictions"]:
                if "Hamilton" in p["driver"]:
                    return p["win_pct"]
            return 0

        dry_win = get_win(canada_prediction, "Hamilton")
        wet_win = get_win(canada_prediction_wet, "Hamilton")
        # Hamilton is a wet-weather specialist — should benefit from rain
        # Allow small margin for simulation noise
        assert wet_win >= dry_win - 1.0, (
            f"Hamilton wet win ({wet_win}) should be >= dry win ({dry_win})"
        )

    def test_metadata_present(self, canada_prediction):
        meta = canada_prediction["meta"]
        for key in ["circuit", "rain_probability", "safety_car_probability", "overall_model_confidence"]:
            assert key in meta

    def test_podium_predictions_length(self, canada_prediction):
        assert len(canada_prediction["podium_predictions"]) == 3

    def test_no_leakage_field(self, canada_prediction):
        """Verify the result does not contain any post-race data fields."""
        forbidden = ["penalty_applied", "post_race_result", "actual_position"]
        for p in canada_prediction["predictions"]:
            for f in forbidden:
                assert f not in p, f"Leakage field '{f}' found in prediction"


# ── Calibration ────────────────────────────────────────────────────────────────

class TestCalibration:
    def test_brier_score_computation(self):
        from engine.calibration import brier_score
        assert brier_score([1.0], [1]) == 0.0
        assert brier_score([0.0], [0]) == 0.0
        assert abs(brier_score([0.5], [1]) - 0.25) < 1e-9

    def test_log_loss_computation(self):
        from engine.calibration import log_loss
        import math
        ll = log_loss([0.9], [1])
        assert ll < 0.2

    def test_platt_scale_returns_tuple(self):
        from engine.calibration import platt_scale
        probs = [0.1, 0.2, 0.5, 0.8, 0.9]
        outcomes = [0, 0, 1, 1, 1]
        A, B = platt_scale(probs, outcomes, n_iter=50)
        assert isinstance(A, float)
        assert isinstance(B, float)

    def test_calibration_report_structure(self):
        from engine.calibration import generate_calibration_report
        probs = [i / 10 for i in range(10)]
        outcomes = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
        report = generate_calibration_report(probs, outcomes, n_bins=5)
        assert len(report) > 0
        for row in report:
            assert "bin" in row
            assert "mean_predicted" in row
            assert "actual_rate" in row
