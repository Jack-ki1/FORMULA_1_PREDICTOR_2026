"""
Feature Engineering Unit Tests — v2.

BUG FIXED vs v1: All references to circuit "bahrain" replaced with "canada".
"bahrain" does not exist in circuit_data.py, causing KeyError on every CI run.

Tests cover:
  - Boundary conditions (0.0 ≤ score ≤ 1.0 for every feature)
  - Graceful handling of invalid driver/circuit IDs (no crashes)
  - Monotonic relationships (more rain → higher score for wet specialists)
  - Determinism (same inputs → same outputs)
  - New v2 features: compute_grid_position_score
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
    compute_grid_position_score,   # new in v2
)
from data.driver_data import get_all_drivers, DRIVERS


# ── Boundary tests ─────────────────────────────────────────────────────────────

class TestBoundaries:
    """Every feature must return a value in [0, 1]."""

    def test_elo_score_bounded(self):
        for d in get_all_drivers():
            s = compute_elo_score(d["id"])
            assert 0.0 <= s <= 1.0, f"ELO out of bounds for {d['id']}: {s}"

    def test_constructor_strength_bounded(self):
        for team in ["mercedes", "ferrari", "mclaren", "red_bull", "haas", "cadillac"]:
            s = compute_constructor_strength(team, "canada")
            assert 0.0 <= s <= 1.0, f"Constructor strength out of bounds for {team}: {s}"

    def test_recent_form_bounded(self):
        for d in get_all_drivers():
            s = compute_recent_form_score(d["id"])
            assert 0.0 <= s <= 1.0

    def test_track_fit_bounded(self):
        for d in get_all_drivers():
            s = compute_track_fit_score(d["id"], "canada")
            assert 0.0 <= s <= 1.0

    def test_reliability_score_bounded(self):
        for d in get_all_drivers():
            s = compute_reliability_score(d["id"])
            assert 0.0 <= s <= 1.0

    def test_dnf_probability_bounded(self):
        for d in get_all_drivers():
            p = estimate_dnf_probability(d["id"])
            assert 0.0 <= p <= 0.45, f"DNF prob out of range for {d['id']}: {p}"

    def test_weather_score_bounded(self):
        for driver_id in ["antonelli", "verstappen", "hamilton", "herta"]:
            for rain in [0.0, 0.5, 1.0]:
                s = compute_weather_score(driver_id, "canada", rain_probability=rain)
                assert 0.0 <= s <= 1.0

    def test_safety_car_upside_bounded(self):
        # FIX: was using "bahrain" — replaced with "canada"
        for grid_pos in [1, 5, 10, 15, 20]:
            s = compute_safety_car_upside("verstappen", "canada", estimated_grid_pos=grid_pos)
            assert 0.0 <= s <= 0.8

    def test_teammate_beat_prob_bounded(self):
        for d in get_all_drivers():
            p = compute_teammate_beat_probability(d["id"])
            assert 0.05 <= p <= 0.95

    def test_composite_score_bounded(self):
        result = compute_composite_score("antonelli", "canada")
        assert 0.0 <= result["composite_score"] <= 1.0

    def test_grid_position_score_bounded(self):
        # No actual grid pos — uses championship proxy
        s = compute_grid_position_score("antonelli")
        assert 0.0 <= s <= 1.0

    def test_grid_position_score_with_actual(self):
        # P1 → near 1.0, P20 → near 0.0
        s_p1  = compute_grid_position_score("antonelli", actual_grid_pos=1)
        s_p20 = compute_grid_position_score("antonelli", actual_grid_pos=20)
        assert s_p1  > 0.90, f"P1 grid score should be near 1.0, got {s_p1}"
        assert s_p20 < 0.10, f"P20 grid score should be near 0.0, got {s_p20}"
        assert s_p1 > s_p20


# ── Monotonic / directional tests ─────────────────────────────────────────────

class TestDirectional:

    def test_wet_specialist_scores_higher_in_wet(self):
        """Hamilton (wet_skill=9.8) must score higher in wet than dry."""
        dry = compute_weather_score("hamilton", "canada", rain_probability=0.05)
        wet = compute_weather_score("hamilton", "canada", rain_probability=0.95)
        assert wet > dry, f"Expected wet>dry for Hamilton, got dry={dry} wet={wet}"

    def test_weather_score_increases_with_rain_monotonically(self):
        scores = [compute_weather_score("hamilton", "canada", rain_probability=r)
                  for r in [0.0, 0.25, 0.5, 0.75, 1.0]]
        assert scores == sorted(scores), f"Not monotonic: {scores}"

    def test_safety_car_upside_increases_with_grid_position(self):
        """Backmarker should benefit more from SC than frontrunner — FIX: was "bahrain"."""
        front = compute_safety_car_upside("verstappen", "canada", estimated_grid_pos=1)
        back  = compute_safety_car_upside("herta",      "canada", estimated_grid_pos=19)
        assert back >= front, f"Back ({back}) should ≥ front ({front})"

    def test_sc_upside_monotonic_across_grid_positions(self):
        """FIX: was using "bahrain" — now uses "canada"."""
        ups = [compute_safety_car_upside("verstappen", "canada", estimated_grid_pos=g)
               for g in [1, 5, 10, 15, 20]]
        assert ups == sorted(ups), f"SC upside should be monotonic with grid pos: {ups}"

    def test_mercedes_stronger_than_cadillac_at_canada(self):
        merc  = compute_constructor_strength("mercedes", "canada")
        caddy = compute_constructor_strength("cadillac", "canada")
        assert merc > caddy

    def test_elo_leader_higher_than_backmarker(self):
        assert compute_elo_score("antonelli") > compute_elo_score("herta")

    def test_grid_p1_better_than_p10(self):
        s1  = compute_grid_position_score("norris", actual_grid_pos=1)
        s10 = compute_grid_position_score("norris", actual_grid_pos=10)
        assert s1 > s10

    def test_dnf_penalty_worse_than_last_place(self):
        """DNF should be penalised more than P20 in form score. v2 uses 25 instead of 21."""
        # Inject a mock to verify: DNF position = N_DRIVERS + 5 = 25
        from engine.feature_engineering import DNF_POSITION_PENALTY, N_DRIVERS
        assert DNF_POSITION_PENALTY > N_DRIVERS, (
            f"DNF penalty {DNF_POSITION_PENALTY} should be > field size {N_DRIVERS}"
        )


# ── Error-handling / graceful degradation tests ───────────────────────────────

class TestGracefulDegradation:
    """Invalid inputs must return neutral values — never raise unhandled exceptions."""

    def test_invalid_driver_elo(self):
        s = compute_elo_score("nonexistent_driver_xyz")
        assert 0.0 <= s <= 1.0

    def test_invalid_circuit_constructor(self):
        s = compute_constructor_strength("mercedes", "nonexistent_circuit_xyz")
        assert 0.05 <= s <= 1.0

    def test_invalid_driver_recent_form(self):
        s = compute_recent_form_score("nonexistent_xyz")
        assert 0.0 <= s <= 1.0

    def test_invalid_driver_weather(self):
        s = compute_weather_score("nonexistent_xyz", "canada")
        assert 0.0 <= s <= 1.0

    def test_invalid_circuit_weather(self):
        s = compute_weather_score("hamilton", "nonexistent_circuit_xyz")
        assert 0.0 <= s <= 1.0

    def test_invalid_driver_track_fit(self):
        s = compute_track_fit_score("nonexistent_xyz", "monaco")
        assert 0.0 <= s <= 1.0

    def test_invalid_driver_reliability(self):
        s = compute_reliability_score("nonexistent_xyz")
        assert 0.0 <= s <= 1.0

    def test_invalid_driver_dnf(self):
        p = estimate_dnf_probability("nonexistent_xyz")
        assert 0.0 <= p <= 0.45

    def test_invalid_driver_sc_upside(self):
        s = compute_safety_car_upside("nonexistent_xyz", "monaco")
        assert 0.0 <= s <= 0.8

    def test_no_teammate_beat_probability(self):
        p = compute_teammate_beat_probability("nonexistent_xyz")
        assert 0.25 <= p <= 0.75  # Near 0.5 when no data


# ── Composite score structure ──────────────────────────────────────────────────

class TestCompositeScore:

    def test_all_expected_feature_keys_present(self):
        result = compute_composite_score("antonelli", "canada")
        expected = [
            "elo_rating", "constructor_strength", "recent_form",
            "track_type_fit", "reliability", "weather_adjustment",
            "safety_car_upside", "grid_position",
        ]
        for k in expected:
            assert k in result["features"], f"Missing feature key: {k}"

    def test_grid_position_no_longer_hardcoded(self):
        """v1 had grid_position always = 0.5. v2 computes it properly."""
        result = compute_composite_score("antonelli", "canada")
        grid_val = result["features"]["grid_position"]
        # Championship leader (P1 → ~P2 after proxy calculation) should be > 0.70
        assert grid_val > 0.65, (
            f"Antonelli grid score {grid_val} — should be high (championship leader)"
        )

    def test_all_feature_values_bounded(self):
        result = compute_composite_score("antonelli", "canada")
        for k, v in result["features"].items():
            assert 0.0 <= float(v) <= 1.0, f"Feature {k} out of bounds: {v}"

    def test_all_drivers_compute_without_error(self):
        results = compute_all_drivers("canada")
        assert len(results) == len(get_all_drivers())

    def test_results_sorted_descending(self):
        results = compute_all_drivers("canada")
        scores = [r["composite_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_deterministic_for_same_inputs(self):
        r1 = compute_all_drivers("canada", rain_probability=0.33)
        r2 = compute_all_drivers("canada", rain_probability=0.33)
        assert [d["driver_id"] for d in r1] == [d["driver_id"] for d in r2]
        assert [d["composite_score"] for d in r1] == [d["composite_score"] for d in r2]

    def test_teammate_beat_probs_near_complement(self):
        """For each team pair, probabilities should sum to ~1.0."""
        seen_teams = set()
        for d_id, d in DRIVERS.items():
            team = d["team"]
            if team in seen_teams:
                continue
            drivers_in_team = [x for x in DRIVERS if DRIVERS[x]["team"] == team]
            if len(drivers_in_team) < 2:
                continue
            p1 = compute_teammate_beat_probability(drivers_in_team[0])
            p2 = compute_teammate_beat_probability(drivers_in_team[1])
            assert abs(p1 + p2 - 1.0) < 0.15, (
                f"Team {team}: {p1} + {p2} = {p1+p2:.3f}, expected ~1.0"
            )
            seen_teams.add(team)

    def test_composite_score_with_actual_grid_override(self):
        """Providing actual grid pos P1 should increase composite vs no override."""
        no_override = compute_composite_score("norris", "canada")["composite_score"]
        with_p1     = compute_composite_score("norris", "canada", actual_grid_pos=1)["composite_score"]
        with_p20    = compute_composite_score("norris", "canada", actual_grid_pos=20)["composite_score"]
        assert with_p1 > no_override > with_p20, (
            f"P1 {with_p1:.4f} should > no_override {no_override:.4f} > P20 {with_p20:.4f}"
        )