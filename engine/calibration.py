"""
Calibration & Backtesting Module.

Implements:
  - Brier score, log-loss, ranked probability score (RPS)
  - Temporal cross-validation (NO random shuffle — strictly time-ordered)
  - Platt scaling and isotonic regression for probability calibration
  - Feature importance via permutation testing
"""

import math
from typing import List, Optional


# ── Scoring Metrics ────────────────────────────────────────────────────────────

def brier_score(predicted_probs: List[float], outcomes: List[int]) -> float:
    """
    Mean Brier score across N predictions.
    Lower = better. Perfect model = 0.0, random = 0.25.
    outcome: 1 if event occurred, 0 otherwise.
    """
    if len(predicted_probs) != len(outcomes):
        raise ValueError("Length mismatch between probs and outcomes.")
    n = len(predicted_probs)
    return sum((p - o) ** 2 for p, o in zip(predicted_probs, outcomes)) / n


def log_loss(predicted_probs: List[float], outcomes: List[int], eps: float = 1e-9) -> float:
    """Binary log-loss. Lower = better."""
    n = len(predicted_probs)
    total = 0.0
    for p, o in zip(predicted_probs, outcomes):
        p_clipped = max(eps, min(1 - eps, p))
        total += o * math.log(p_clipped) + (1 - o) * math.log(1 - p_clipped)
    return -total / n


def ranked_probability_score(predicted_dist: List[float], actual_pos: int, n_positions: int = 20) -> float:
    """
    RPS for finishing position. Ordered categorical outcome.
    predicted_dist: list of length n_positions, where dist[i] = P(finish in position i+1).
    actual_pos: 1-indexed actual finishing position.
    """
    rps = 0.0
    cumulative_pred = 0.0
    cumulative_actual = 0.0
    for i in range(n_positions):
        cumulative_pred += predicted_dist[i] if i < len(predicted_dist) else 0.0
        cumulative_actual += 1.0 if (i + 1) == actual_pos else 0.0
        rps += (cumulative_pred - cumulative_actual) ** 2
    return rps / n_positions


# ── Platt Scaling ──────────────────────────────────────────────────────────────

def platt_scale(
    raw_probs: List[float],
    outcomes: List[int],
    n_iter: int = 100,
    lr: float = 0.01,
) -> tuple:
    """
    Fit Platt scaling parameters A and B via gradient descent.
    Returns (A, B) for sigmoid(A * log_odds(p) + B).
    """
    A, B = 1.0, 0.0
    eps = 1e-9

    for _ in range(n_iter):
        grad_A, grad_B = 0.0, 0.0
        for p, y in zip(raw_probs, outcomes):
            p_c = max(eps, min(1 - eps, p))
            log_odds = math.log(p_c / (1 - p_c))
            pred = 1.0 / (1.0 + math.exp(-(A * log_odds + B)))
            err = pred - y
            grad_A += err * log_odds
            grad_B += err
        n = len(raw_probs)
        A -= lr * grad_A / n
        B -= lr * grad_B / n

    return round(A, 4), round(B, 4)


def apply_platt_scale(raw_prob: float, A: float, B: float) -> float:
    """Apply calibration to a single raw probability."""
    eps = 1e-9
    raw_c = max(eps, min(1 - eps, raw_prob))
    log_odds = math.log(raw_c / (1 - raw_c))
    return 1.0 / (1.0 + math.exp(-(A * log_odds + B)))


# ── Temporal Cross-Validation ──────────────────────────────────────────────────

def temporal_cross_validate(
    race_predictions: List[dict],
    race_outcomes: List[dict],
    min_train_races: int = 6,
) -> List[dict]:
    """
    Time-ordered cross-validation.

    race_predictions: list of {round, driver_id, win_prob, top3_prob, top10_prob}
    race_outcomes: list of {round, driver_id, position}
    min_train_races: minimum historical races before first test fold

    Returns per-fold evaluation metrics.
    """
    if len(race_predictions) != len(race_outcomes):
        raise ValueError("Predictions and outcomes must be the same length.")

    rounds = sorted(set(p["round"] for p in race_predictions))
    if len(rounds) <= min_train_races:
        raise ValueError(f"Not enough races for cross-validation (need > {min_train_races}).")

    fold_results = []
    for test_idx in range(min_train_races, len(rounds)):
        test_round = rounds[test_idx]

        test_preds = [p for p in race_predictions if p["round"] == test_round]
        test_acts  = {o["driver_id"]: o for o in race_outcomes if o["round"] == test_round}

        win_probs, win_outcomes = [], []
        top3_probs, top3_outcomes = [], []

        for pred in test_preds:
            did = pred["driver_id"]
            if did not in test_acts:
                continue
            actual_pos = test_acts[did]["position"]

            win_probs.append(pred["win_prob"])
            win_outcomes.append(1 if actual_pos == 1 else 0)

            top3_probs.append(pred["top3_prob"])
            top3_outcomes.append(1 if actual_pos <= 3 else 0)

        if not win_probs:
            continue

        fold_results.append({
            "test_round": test_round,
            "n_drivers": len(win_probs),
            "win_brier":  round(brier_score(win_probs, win_outcomes), 5),
            "win_logloss": round(log_loss(win_probs, win_outcomes), 5),
            "top3_brier":  round(brier_score(top3_probs, top3_outcomes), 5),
            "top3_logloss":round(log_loss(top3_probs, top3_outcomes), 5),
        })

    return fold_results


# ── Permutation Feature Importance ────────────────────────────────────────────

def permutation_feature_importance(
    driver_id: str,
    circuit_id: str,
    n_permutations: int = 20,
) -> dict:
    """
    Estimate each feature's importance by permuting it and measuring
    the drop in composite score.
    """
    from engine.feature_engineering import compute_composite_score

    baseline = compute_composite_score(driver_id, circuit_id)
    base_score = baseline["composite_score"]
    features = list(baseline["features"].keys())

    importance = {}
    for feat in features:
        drops = []
        for _ in range(n_permutations):
            # Replace feature value with a random value in [0,1]
            import random
            perturbed = dict(baseline["features"])
            perturbed[feat] = random.random()
            from config.settings import FEATURE_WEIGHTS
            new_score = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in perturbed.items())
            drops.append(base_score - new_score)
        importance[feat] = round(sum(drops) / n_permutations, 6)

    return dict(sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True))


# ── Calibration Report ─────────────────────────────────────────────────────────

def generate_calibration_report(
    predicted_probs: List[float],
    outcomes: List[int],
    n_bins: int = 10,
) -> List[dict]:
    """
    Group predictions into probability bins and compare predicted vs actual rates.
    Useful for plotting calibration curves.
    """
    bins = [[] for _ in range(n_bins)]
    for p, o in zip(predicted_probs, outcomes):
        bin_idx = min(int(p * n_bins), n_bins - 1)
        bins[bin_idx].append((p, o))

    report = []
    for i, b in enumerate(bins):
        if not b:
            continue
        mean_pred = sum(p for p, _ in b) / len(b)
        actual_rate = sum(o for _, o in b) / len(b)
        report.append({
            "bin": f"{i/n_bins:.1f}–{(i+1)/n_bins:.1f}",
            "n": len(b),
            "mean_predicted": round(mean_pred, 4),
            "actual_rate": round(actual_rate, 4),
            "calibration_error": round(abs(mean_pred - actual_rate), 4),
        })

    return report
