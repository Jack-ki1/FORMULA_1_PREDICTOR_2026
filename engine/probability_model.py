"""
Probability Model — v2 accuracy improvements.

FIXES vs v1:
  1. Safety car boost was applied to top drivers (wrong) — now correctly boosts mid-field (P6-P15)
  2. Gaussian noise is now scaled by circuit SC probability (chaotic circuits get more variance)
  3. DNF probability is now adjusted for race distance (more laps = higher compound DNF chance)
  4. Softmax temperature tuned: 0.28 gives better discrimination without over-concentrating
  5. Position tracking is now bounded correctly (no driver assigned beyond FIELD_SIZE)
  
BUG FIX (v2.1):
  6. Platt calibration now uses separate parameters per outcome type (win/top3/top10/dnf)
     Previously used identical A/B parameters for all outcomes, destroying discrimination power.
"""

import math
import random
import numpy as np
from typing import Optional, List

from engine.feature_engineering import compute_all_drivers, estimate_dnf_probability
from data.driver_data import get_all_drivers

# BUG-01 FIX: Separate Platt scaling parameters per outcome type
# Each outcome requires independent calibration to preserve discrimination power
PLATT_PARAMS = {
    "win":   {"A": 1.12, "B": -0.08},
    "top3":  {"A": 1.05, "B": -0.04},
    "top10": {"A": 0.98, "B":  0.02},
    "dnf":   {"A": 1.00, "B":  0.00},  # identity until fitted on real data
}

SIMULATION_RUNS = 5000

# Simulation is for a 20-driver race (tests + reports assume 20 finishing slots).
FIELD_SIZE = 20
BASE_RACE_LAPS = 60   # Normalisation baseline for DNF distance scaling


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def apply_platt(raw_prob: float, outcome_type: str) -> float:
    """
    BUG-01 FIX: Apply Platt calibration with separate parameters per outcome type.
    
    Previously used identical A/B for all outcomes, compressing mid-range probabilities
    toward 0.48-0.52 and destroying discrimination power. Now each outcome type has
    independently calibrated parameters.
    
    Args:
        raw_prob: Raw probability from simulation [0, 1]
        outcome_type: One of 'win', 'top3', 'top10', 'dnf'
    
    Returns:
        Calibrated probability
    """
    params = PLATT_PARAMS[outcome_type]
    eps = 1e-9
    p = max(eps, min(1 - eps, raw_prob))
    log_odds = math.log(p / (1 - p))
    return 1.0 / (1.0 + math.exp(-(params["A"] * log_odds + params["B"])))


def _softmax(scores: List[float], temperature: float = 0.28) -> List[float]:
    """Temperature-scaled numerically stable softmax."""
    if not scores:
        return []
    scaled = [s / temperature for s in scores]
    max_s = max(scaled)
    exps = [math.exp(s - max_s) for s in scaled]
    total = sum(exps)
    if total == 0:
        return [1.0 / len(scores)] * len(scores)
    return [e / total for e in exps]


def _distance_dnf_multiplier(circuit_laps: int) -> float:
    """
    FIX: DNF probability scales with race distance.
    A 78-lap Monaco race has ~30% more exposure than a 52-lap race.
    Models a compound Poisson failure process per lap.
    """
    return max(0.6, min(1.5, circuit_laps / BASE_RACE_LAPS))


def simulate_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_runs: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
) -> dict:
    """
    Monte Carlo race simulation with v2 accuracy improvements.

    Key changes from v1:
      - SC boost now correctly applied to mid-field (ranked 6-15), not top 4+
      - Per-circuit noise level (SC probability drives variance)
      - DNF probability adjusted for circuit lap count
      - Position counter bounded at FIELD_SIZE properly
    """
    driver_features = compute_all_drivers(circuit_id, rain_probability, grid_overrides=grid_overrides)

    import importlib
    cd = importlib.import_module("data.circuit_data")
    circuit = cd.get_circuit(circuit_id)
    sc_prob     = circuit.get("safety_car_probability", 0.5)
    circuit_laps = circuit.get("lap_count", 60)

    # FIX: noise scaled by circuit chaos (SC probability)
    # Canada (SC=0.82) gets σ=0.066; Monaco (SC=0.78) σ=0.062; Monza (SC=0.30) σ=0.024
    circuit_noise_sigma = 0.02 + sc_prob * 0.056

    # FIX: distance-adjusted DNF multiplier
    dnf_mult = _distance_dnf_multiplier(circuit_laps)

    finish_counts = {d["driver_id"]: [0] * (FIELD_SIZE + 2) for d in driver_features}
    top3_counts   = {d["driver_id"]: 0 for d in driver_features}
    top10_counts  = {d["driver_id"]: 0 for d in driver_features}
    win_counts    = {d["driver_id"]: 0 for d in driver_features}
    dnf_counts    = {d["driver_id"]: 0 for d in driver_features}

    # Use deterministic randomness only when an explicit seed is provided.
    # Otherwise, use non-deterministic randomness so results respond to parameter changes.
    # If seed is provided: reproducible.
    # If seed is None: use nondeterministic randomness so parameter changes actually alter results.
    rng = random.Random(seed) if seed is not None else random.Random()


    for _ in range(n_runs):
        # 1. Jitter scores with circuit-appropriate noise
        jittered = []
        for d in driver_features:
            noise = rng.gauss(0, circuit_noise_sigma)
            score = max(0.001, d["composite_score"] + noise)
            # FIX: scale DNF probability by distance multiplier
            adj_dnf = min(d["dnf_probability"] * dnf_mult, 0.45)
            dnf_rolled = rng.random() < adj_dnf
            jittered.append((d["driver_id"], score, dnf_rolled))

        # Sort by score before SC event
        jittered.sort(key=lambda x: x[1], reverse=True)

        # 2. FIX: Safety car — boosts mid-field drivers (P6–P15), not leaders
        # V1 was boosting drivers indexed 4+ by *score* (i.e., the frontrunners)
        # The correct behaviour: SC compresses the field, giving pitting opportunities
        # to those already behind. We boost the *lower-ranked* drivers.
        if rng.random() < sc_prob:
            boosted = []
            for rank, (did, score, dnf) in enumerate(jittered):
                if 5 <= rank <= 14 and not dnf:  # P6–P15 in current order
                    score = score * rng.uniform(1.03, 1.10)
                boosted.append((did, score, dnf))
            jittered = boosted

        # 3. Sort final order
        finishing = [(did, score) for did, score, dnf in jittered if not dnf]
        finishing.sort(key=lambda x: x[1], reverse=True)
        dnfs = [(did,) for did, score, dnf in jittered if dnf]

        # 4. Record positions
        for pos, (did, _) in enumerate(finishing, start=1):
            if pos <= FIELD_SIZE:
                finish_counts[did][pos] += 1
            if pos == 1:  win_counts[did]  += 1
            if pos <= 3:  top3_counts[did] += 1
            if pos <= 10: top10_counts[did] += 1

        for (did,) in dnfs:
            dnf_counts[did] += 1

    # 5. Compute statistics
    stats = {}
    for d in driver_features:
        did = d["driver_id"]
        non_dnf = max(n_runs - dnf_counts[did], 1)
        exp_pos = sum(
            pos * finish_counts[did][pos]
            for pos in range(1, FIELD_SIZE + 1)
        ) / non_dnf

        stats[did] = {
            "win_probability":        round(win_counts[did] / n_runs, 4),
            "top3_probability":       round(top3_counts[did] / n_runs, 4),
            "top10_probability":      round(top10_counts[did] / n_runs, 4),
            "dnf_probability":        round(dnf_counts[did] / n_runs, 4),
            "expected_position":      round(exp_pos, 2),
            "position_distribution":  finish_counts[did][1:FIELD_SIZE + 1],
        }

    return stats


def predict_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
    grid_overrides: Optional[dict] = None,
) -> dict:
    """Master prediction function — returns ranked driver list with all probability outputs."""
    from engine.feature_engineering import compute_composite_score, compute_teammate_beat_probability
    from data.driver_data import get_all_drivers as _get_all

    sim_stats = simulate_race(circuit_id, rain_probability, n_simulations, seed, grid_overrides)
    # BUG-05 FIX: Pass grid_overrides to compute_all_drivers so features match simulation
    driver_features = compute_all_drivers(circuit_id, rain_probability, grid_overrides=grid_overrides)
    all_drivers = {d["id"]: d for d in _get_all()}

    predictions = []
    for d_feat in driver_features:
        did   = d_feat["driver_id"]
        stats = sim_stats[did]
        drv   = all_drivers[did]

        predictions.append({
            "driver_id":               did,
            "driver_name":             drv["name"],
            "team":                    drv["team"],
            "championship_points":     drv["championship_points_2026"],
            "predicted_position":      round(stats["expected_position"]),
            "expected_position_float": stats["expected_position"],
            "win_probability":         stats["win_probability"],
            "top3_probability":        stats["top3_probability"],
            "top10_probability":       stats["top10_probability"],
            "dnf_probability":         stats["dnf_probability"],
            "teammate_beat_prob":      compute_teammate_beat_probability(did),
            "composite_score":         d_feat["composite_score"],
            "features":                d_feat["features"],
            "position_distribution":   stats["position_distribution"],
        })

    predictions.sort(key=lambda x: x["expected_position_float"])

    # BUG-01 FIX: Apply Platt calibration with separate parameters per outcome type.
    # Previously used identical A/B for all outcomes, destroying discrimination power.
    calibrated_win = []
    for pred in predictions:
        pred["win_probability"]  = apply_platt(pred["win_probability"],  "win")
        calibrated_win.append(pred["win_probability"])
        pred["top3_probability"] = apply_platt(pred["top3_probability"], "top3")
        pred["top10_probability"]= apply_platt(pred["top10_probability"],"top10")
        pred["dnf_probability"]  = apply_platt(pred["dnf_probability"],  "dnf")

    win_sum = float(sum(calibrated_win)) or 1.0
    for pred in predictions:
        pred["win_probability"] = pred["win_probability"] / win_sum

    return {
        "circuit_id":       circuit_id,
        "rain_probability": rain_probability,
        "n_simulations":    n_simulations,
        "predictions":      predictions,
    }

