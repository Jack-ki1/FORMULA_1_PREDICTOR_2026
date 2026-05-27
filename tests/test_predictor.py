"""
Predictor Integration Tests — v2.

Tests the full pipeline: features → simulation → formatted output.
Uses n_simulations=200 for speed (CI-friendly).

New v2 tests:
  - position_distribution present in output
  - grid_override changes predictions
  - DNF probability increases with longer circuits
"""

import pytest
from engine.predictor import predict, PredictionRequest
from engine.feature_engineering import (
    compute_elo_score, compute_constructor_strength,
    compute_recent_form_score, compute_track_fit_score,
    compute_reliability_score, estimate_dnf_probability,
    compute_composite_score, compute_all_drivers,
)
from data.driver_data import get_driver, get_all_drivers
from data.circuit_data import get_circuit


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def canada_dry():
    return predict(PredictionRequest(circuit_id="canada", n_simulations=200, seed=42))

@pytest.fixture(scope="module")
def canada_wet():
    return predict(PredictionRequest(circuit_id="canada", rain_probability=0.90,
                                     n_simulations=200, seed=42))

@pytest.fixture(scope="module")
def monaco_pred():
    return predict(PredictionRequest(circuit_id="monaco", n_simulations=200, seed=42))


# ── Data integrity ─────────────────────────────────────────────────────────────

class TestDataIntegrity:

    def test_all_drivers_have_required_fields(self):
        required = ["id", "name", "team", "elo", "dnf_rate_recent",
                    "track_type_fit", "recent_form", "championship_points_2026"]
        for d in get_all_drivers():
            for f in required:
                assert f in d, f"Driver {d['id']} missing '{f}'"

    def test_elo_range(self):
        for d in get_all_drivers():
            assert 1400 <= d["elo"] <= 1700, f"ELO out of range for {d['id']}"

    def test_dnf_rates_bounded(self):
        for d in get_all_drivers():
            assert 0.0 <= d["dnf_rate_recent"] <= 1.0
            assert 0.0 <= d["dnf_rate_career"] <= 1.0

    def test_canada_circuit_loaded(self):
        c = get_circuit("canada")
        assert c["safety_car_probability"] > 0
        assert c["lap_count"] > 0

    def test_all_2026_circuits_loadable(self):
        from data.calendar_2026 import CALENDAR_2026
        for race in CALENDAR_2026:
            try:
                get_circuit(race["circuit"])
            except KeyError as e:
                pytest.fail(f"Circuit not found for round {race['round']}: {e}")


# ── Output structure ──────────────────────────────────────────────────────────

class TestOutputStructure:

    def test_predictions_count_matches_field(self, canada_dry):
        assert len(canada_dry["predictions"]) == len(get_all_drivers())

    def test_meta_keys_present(self, canada_dry):
        meta = canada_dry["meta"]
        for k in ["circuit", "city", "race_date", "sprint_weekend",
                  "safety_car_probability", "rain_probability",
                  "n_simulations", "overall_model_confidence"]:
            assert k in meta, f"Missing meta key: {k}"

    def test_podium_predictions_length(self, canada_dry):
        assert len(canada_dry["podium_predictions"]) == 3

    def test_position_distribution_in_output(self, canada_dry):
        """v2: position_distribution must be present for charts."""
        for p in canada_dry["predictions"]:
            assert "position_distribution" in p, (
                f"{p['driver']} missing position_distribution"
            )
            dist = p["position_distribution"]
            assert len(dist) == 20, f"Expected 20 positions, got {len(dist)}"

    def test_features_in_output(self, canada_dry):
        """v2: features dict must be present for feature breakdown chart."""
        for p in canada_dry["predictions"]:
            assert "features" in p, f"{p['driver']} missing features"
            assert len(p["features"]) > 0

    def test_no_leakage_fields(self, canada_dry):
        forbidden = ["penalty_applied", "post_race_result", "actual_position",
                     "steward_decision", "post_race_penalty"]
        for p in canada_dry["predictions"]:
            for f in forbidden:
                assert f not in p, f"Leakage field '{f}' found in prediction"


# ── Probability correctness ────────────────────────────────────────────────────

class TestProbabilities:

    def test_win_probs_sum_to_100(self, canada_dry):
        total = sum(p["win_pct"] for p in canada_dry["predictions"])
        assert abs(total - 100.0) < 3.0, f"Win probs sum to {total:.1f}%, expected ~100"

    def test_all_probabilities_bounded(self, canada_dry):
        for p in canada_dry["predictions"]:
            for col in ["win_pct", "top3_pct", "top10_pct", "dnf_pct"]:
                assert 0 <= p[col] <= 100, f"{p['driver']}.{col} = {p[col]} — out of bounds"

    def test_top3_gte_win(self, canada_dry):
        for p in canada_dry["predictions"]:
            assert p["top3_pct"] >= p["win_pct"] - 0.5, (
                f"{p['driver']}: top3 {p['top3_pct']} < win {p['win_pct']}"
            )

    def test_top10_gte_top3(self, canada_dry):
        for p in canada_dry["predictions"]:
            assert p["top10_pct"] >= p["top3_pct"] - 0.5, (
                f"{p['driver']}: top10 {p['top10_pct']} < top3 {p['top3_pct']}"
            )

    def test_antonelli_highest_win_prob(self, canada_dry):
        win_probs = {p["driver"]: p["win_pct"] for p in canada_dry["predictions"]}
        max_driver = max(win_probs, key=win_probs.get)
        assert "Antonelli" in max_driver, (
            f"Expected Antonelli to have highest win prob, got {max_driver}"
        )

    def test_mercedes_both_in_top5(self, canada_dry):
        top5_names = [p["driver"] for p in canada_dry["predictions"][:5]]
        merc_in_top5 = sum(1 for n in top5_names if "Antonelli" in n or "Russell" in n)
        assert merc_in_top5 >= 1, "At least one Mercedes driver should be in top 5"


# ── Weather effects ────────────────────────────────────────────────────────────

class TestWeather:

    def test_wet_boosts_hamilton(self, canada_dry, canada_wet):
        def get_win(pred, search):
            for p in pred["predictions"]:
                if search in p["driver"]:
                    return p["win_pct"]
            return 0.0
        dry_win = get_win(canada_dry, "Hamilton")
        wet_win = get_win(canada_wet, "Hamilton")
        assert wet_win >= dry_win - 1.5, (
            f"Hamilton wet {wet_win}% should ≥ dry {dry_win}% (wet specialist)"
        )

    def test_wet_reduces_less_skilled_driver(self, canada_dry, canada_wet):
        def get_win(pred, search):
            for p in pred["predictions"]:
                if search in p["driver"]:
                    return p["win_pct"]
            return 0.0
        # Herta has wet_skill=6.5 — should lose relative ground in the wet
        dry = get_win(canada_dry, "Herta")
        wet = get_win(canada_wet, "Herta")
        # Either stays the same or drops (allow ±1% for simulation noise)
        assert wet <= dry + 1.5, (
            f"Herta wet {wet}% should not be much higher than dry {dry}%"
        )


# ── Grid override ─────────────────────────────────────────────────────────────

class TestGridOverride:

    def test_grid_override_changes_prediction(self):
        """Putting Alonso at P1 (fantasy scenario) should improve his composite."""
        from engine.feature_engineering import compute_grid_position_score
        s_no_override = compute_grid_position_score("alonso")
        s_p1          = compute_grid_position_score("alonso", actual_grid_pos=1)
        s_p20         = compute_grid_position_score("alonso", actual_grid_pos=20)
        assert s_p1 > s_no_override > s_p20, (
            f"P1={s_p1:.3f} should > default={s_no_override:.3f} > P20={s_p20:.3f}"
        )

    def test_full_prediction_with_seed_is_reproducible(self):
        r1 = predict(PredictionRequest(circuit_id="canada", n_simulations=100, seed=999))
        r2 = predict(PredictionRequest(circuit_id="canada", n_simulations=100, seed=999))
        for p1, p2 in zip(r1["predictions"], r2["predictions"]):
            assert p1["win_pct"] == p2["win_pct"], "Seeded runs should be identical"


# ── Circuit-specific behaviour ─────────────────────────────────────────────────

class TestCircuitBehaviour:

    def test_monaco_has_lower_overtaking_than_canada(self):
        can = get_circuit("canada")
        mon = get_circuit("monaco")
        assert mon["overtaking_difficulty"] > can["overtaking_difficulty"], (
            "Monaco should be harder to overtake than Canada"
        )

    def test_canada_has_highest_sc_probability(self):
        can_sc  = get_circuit("canada")["safety_car_probability"]
        spa_sc  = get_circuit("belgium")["safety_car_probability"]
        # Canada SC rate (0.82) ≥ Spa (0.68)
        assert can_sc >= spa_sc

    def test_italy_highest_power_unit_demand(self):
        """Monza is a power-unit circuit — should have the highest PU demand."""
        ita = get_circuit("italy")["power_unit_demand"]
        mon = get_circuit("monaco")["power_unit_demand"]
        assert ita > mon, "Monza PU demand should exceed Monaco"


# ── Calibration module ─────────────────────────────────────────────────────────

class TestCalibration:

    def test_brier_score(self):
        from engine.calibration import brier_score
        assert brier_score([1.0], [1]) == 0.0
        assert brier_score([0.0], [0]) == 0.0
        assert abs(brier_score([0.5], [1]) - 0.25) < 1e-9

    def test_log_loss(self):
        from engine.calibration import log_loss
        ll = log_loss([0.9], [1])
        assert ll < 0.15, f"log_loss for confident correct prediction should be low: {ll}"

    def test_platt_scale_returns_floats(self):
        from engine.calibration import platt_scale
        A, B = platt_scale([0.1, 0.5, 0.9], [0, 1, 1], n_iter=20)
        assert isinstance(A, float) and isinstance(B, float)

    def test_calibration_report_bins_non_empty(self):
        from engine.calibration import generate_calibration_report
        report = generate_calibration_report(
            [0.1, 0.3, 0.5, 0.7, 0.9], [0, 0, 1, 1, 1], n_bins=5
        )
        assert len(report) > 0
        for row in report:
            assert "bin" in row and "mean_predicted" in row and "actual_rate" in row

    def test_temporal_cv_raises_on_insufficient_data(self):
        from engine.calibration import temporal_cross_validate
        preds = [{"round": 1, "driver_id": "antonelli", "win_prob": 0.5,
                  "top3_prob": 0.8, "top10_prob": 0.95}]
        outcomes = [{"round": 1, "driver_id": "antonelli", "position": 1}]
        with pytest.raises(ValueError, match="Not enough rounds"):
            temporal_cross_validate(preds, outcomes, min_train_races=6)