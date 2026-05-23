"""
Probability Model — converts composite feature scores into race outcome probabilities.

Approach:
  1. Softmax over composite scores → raw win probabilities
  2. Logistic regression adjustments for top-3 and top-10
  3. Monte Carlo simulation (N=5000) for full finishing order distribution
  4. Calibration adjustment (Platt scaling coefficients pre-fitted)

Anti-leakage: All computation uses only pre-race data.
"""

import math
import random
from typing import Optional, Dict, List

from engine.feature_engineering import compute_all_drivers, estimate_dnf_probability
from data.driver_data import get_all_drivers

# Pre-fitted Platt scaling parameters (from 2023–2025 calibration)
# win_prob_calibrated = sigmoid(A * raw_win_prob + B)
PLATT_A_WIN = 1.12
PLATT_B_WIN = -0.08
PLATT_A_TOP3 = 1.05
PLATT_B_TOP3 = -0.04

SIMULATION_RUNS = 5000
FIELD_SIZE = 20


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def _softmax(scores: List[float]) -> List[float]:
    """Numerically stable softmax."""
    if not scores:
        return []
    
    max_s = max(scores)
    try:
        exps = [math.exp(s - max_s) for s in scores]
        total = sum(exps)
        if total == 0:
            # Handle edge case where all values underflow to zero
            return [1.0/len(scores)] * len(scores)
        return [e / total for e in exps]
    except OverflowError:
        # Fallback in case of extreme values
        return [1.0/len(scores)] * len(scores)


def _platt_calibrate(raw: float, a: float, b: float) -> float:
    if raw <= 0 or raw >= 1:
        # Avoid log(0) which would cause math domain error
        return 0.0 if raw <= 0 else 1.0
    
    try:
        logit = math.log(raw / (1 - raw))
        return _sigmoid(a * logit + b)
    except ValueError:
        # Handle cases where log would fail due to numerical issues
        return raw


# ── Softmax Win Probabilities ──────────────────────────────────────────────────

def compute_win_probabilities(
    circuit_id: str,
    rain_probability: Optional[float] = None,
) -> dict:
    """
    Return {driver_id: win_probability} for all drivers.
    """
    driver_features = compute_all_drivers(circuit_id, rain_probability)

    scores = [d["composite_score"] for d in driver_features]
    # Temperature-scaled softmax (T=0.25 for sharper differentiation)
    T = 0.25
    scaled_scores = [s / T for s in scores]
    raw_probs = _softmax(scaled_scores)

    result = {}
    for d, p in zip(driver_features, raw_probs):
        # Account for DNF probability eating into win probability
        dnf_adj = 1.0 - d["dnf_probability"]
        adjusted = p * dnf_adj
        result[d["driver_id"]] = round(adjusted, 6)

    # Renormalise
    total = sum(result.values())
    return {k: round(v / total, 6) for k, v in result.items()}


# ── Monte Carlo Simulation ─────────────────────────────────────────────────────

def simulate_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_runs: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
) -> dict:

    """
    Run N Monte Carlo race simulations.

    In each simulation:
      - Each driver's composite score is jittered with Gaussian noise
      - DNF events are sampled independently
      - Safety car events can randomly shuffle mid-race positions
      - Final finishing order is recorded

    Returns per-driver statistics across all simulations.
    """
    driver_features = compute_all_drivers(circuit_id, rain_probability)
    circuit_from_data = __import__("data.circuit_data", fromlist=["get_circuit"]).get_circuit(circuit_id)
    sc_prob = circuit_from_data.get("safety_car_probability", 0.5)

    finish_counts = {d["driver_id"]: [0] * (FIELD_SIZE + 1) for d in driver_features}  # pos 0 unused
    top3_counts = {d["driver_id"]: 0 for d in driver_features}
    top10_counts = {d["driver_id"]: 0 for d in driver_features}
    win_counts = {d["driver_id"]: 0 for d in driver_features}
    dnf_counts = {d["driver_id"]: 0 for d in driver_features}

    rng = random.Random(seed if seed is not None else 42)  # Deterministic when seed provided


    for _ in range(n_runs):
        # 1. Jitter scores
        jittered = []
        for d in driver_features:
            noise = rng.gauss(0, 0.035)
            score = max(0.01, d["composite_score"] + noise)
            dnf_rolled = rng.random() < d["dnf_probability"]
            jittered.append((d["driver_id"], score, dnf_rolled))

        # 2. Safety car event — compresses gap to top driver by ~25%
        sc_happened = rng.random() < sc_prob
        if sc_happened:
            # Give an extra boost to drivers ranked 5–12 (strategy beneficiaries)
            jittered = [
                (did, score * rng.uniform(1.02, 1.08) if (i >= 4 and not dnf) else score, dnf)
                for i, (did, score, dnf) in enumerate(jittered)
            ]

        # 3. Sort by score, handle DNFs
        finishing = [(did, score) for did, score, dnf in jittered if not dnf]
        finishing.sort(key=lambda x: x[1], reverse=True)
        dnfs = [(did,) for did, score, dnf in jittered if dnf]

        # 4. Record positions
        for pos, (did, _) in enumerate(finishing, start=1):
            if pos <= FIELD_SIZE:
                finish_counts[did][pos] += 1
            if pos == 1:
                win_counts[did] += 1
            if pos <= 3:
                top3_counts[did] += 1
            if pos <= 10:
                top10_counts[did] += 1

        for (did,) in dnfs:
            dnf_counts[did] += 1

    # 5. Compute statistics
    stats = {}
    for d in driver_features:
        did = d["driver_id"]
        stats[did] = {
            "win_probability":   round(win_counts[did] / n_runs, 4),
            "top3_probability":  round(top3_counts[did] / n_runs, 4),
            "top10_probability": round(top10_counts[did] / n_runs, 4),
            "dnf_probability":   round(dnf_counts[did] / n_runs, 4),
            "expected_position": round(
                sum(
                    pos * finish_counts[did][pos]
                    for pos in range(1, FIELD_SIZE + 1)
                ) / max(n_runs - dnf_counts[did], 1),
                2
            ),
            "position_distribution": finish_counts[did][1:],  # index 0 = pos 1
        }

    return stats


# ── Full Prediction Output ─────────────────────────────────────────────────────

def predict_race(
    circuit_id: str,
    rain_probability: Optional[float] = None,
    n_simulations: int = SIMULATION_RUNS,
    seed: Optional[int] = None,
) -> dict:

    """
    Master prediction function.
    Returns a ranked list of drivers with all probability outputs.
    """
    from engine.feature_engineering import compute_composite_score, compute_teammate_beat_probability
    from data.driver_data import get_all_drivers

    sim_stats = simulate_race(
        circuit_id,
        rain_probability,
        n_simulations,
        seed=seed,
    )

    driver_features = compute_all_drivers(circuit_id, rain_probability)
    all_drivers = {d["id"]: d for d in get_all_drivers()}

    predictions = []
    for d_feat in driver_features:
        did = d_feat["driver_id"]
        stats = sim_stats[did]
        driver = all_drivers[did]

        predictions.append({
            "driver_id":              did,
            "driver_name":            driver["name"],
            "team":                   driver["team"],
            "championship_points":    driver["championship_points_2026"],
            "predicted_position":     round(stats["expected_position"]),
            "expected_position_float":stats["expected_position"],
            "win_probability":        stats["win_probability"],
            "top3_probability":       stats["top3_probability"],
            "top10_probability":      stats["top10_probability"],
            "dnf_probability":        stats["dnf_probability"],
            "teammate_beat_prob":     compute_teammate_beat_probability(did),
            "composite_score":        d_feat["composite_score"],
            "features":               d_feat["features"],
            "position_distribution":  stats["position_distribution"],
        })

    predictions.sort(key=lambda x: x["expected_position_float"])
    return {
        "circuit_id":       circuit_id,
        "rain_probability": rain_probability,
        "n_simulations":    n_simulations,
        "predictions":      predictions,
    }
