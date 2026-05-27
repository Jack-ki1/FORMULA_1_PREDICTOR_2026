"""
Calibration & Backtesting — v2.

FIX: temporal_cross_validate used strict length equality check which crashed
when rounds had different driver counts. Replaced with round-by-round join.
"""

import math
from typing import List, Optional


def brier_score(predicted_probs: List[float], outcomes: List[int]) -> float:
    """Mean Brier score. Lower = better. Perfect = 0.0, random ≈ 0.25."""
    if not predicted_probs:
        raise ValueError("Empty probability list.")
    n = len(predicted_probs)
    return sum((p - o) ** 2 for p, o in zip(predicted_probs, outcomes)) / n


def log_loss(predicted_probs: List[float], outcomes: List[int], eps: float = 1e-9) -> float:
    """Binary log-loss. Lower = better."""
    n = len(predicted_probs)
    total = 0.0
    for p, o in zip(predicted_probs, outcomes):
        p_c = max(eps, min(1 - eps, p))
        total += o * math.log(p_c) + (1 - o) * math.log(1 - p_c)
    return -total / n


def ranked_probability_score(predicted_dist: List[float], actual_pos: int,
                              n_positions: int = 20) -> float:
    """RPS — ordered categorical outcome accuracy."""
    rps, cum_pred, cum_actual = 0.0, 0.0, 0.0
    for i in range(n_positions):
        cum_pred   += predicted_dist[i] if i < len(predicted_dist) else 0.0
        cum_actual += 1.0 if (i + 1) == actual_pos else 0.0
        rps += (cum_pred - cum_actual) ** 2
    return rps / n_positions


def platt_scale(raw_probs: List[float], outcomes: List[int],
                n_iter: int = 100, lr: float = 0.01) -> tuple:
    """Fit Platt scaling A, B via gradient descent."""
    A, B = 1.0, 0.0
    eps = 1e-9
    for _ in range(n_iter):
        grad_A = grad_B = 0.0
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
    eps = 1e-9
    raw_c = max(eps, min(1 - eps, raw_prob))
    log_odds = math.log(raw_c / (1 - raw_c))
    return 1.0 / (1.0 + math.exp(-(A * log_odds + B)))


def temporal_cross_validate(
    race_predictions: List[dict],
    race_outcomes: List[dict],
    min_train_races: int = 6,
) -> List[dict]:
    """
    Time-ordered cross-validation.

    FIX vs v1: Replaced strict `len(preds) != len(outcomes)` check with a
    round-by-round join. This handles cases where some rounds have fewer
    driver entries (e.g. early season with fewer completed rounds).

    race_predictions: [{round, driver_id, win_prob, top3_prob, top10_prob}, ...]
    race_outcomes:    [{round, driver_id, position}, ...]
    """
    rounds = sorted(set(p["round"] for p in race_predictions))
    if len(rounds) <= min_train_races:
        raise ValueError(
            f"Not enough rounds for CV. Have {len(rounds)}, need > {min_train_races}."
        )

    # Build outcome lookup: (round, driver_id) → position
    outcome_map = {(o["round"], o["driver_id"]): o["position"] for o in race_outcomes}

    fold_results = []
    for test_idx in range(min_train_races, len(rounds)):
        test_round = rounds[test_idx]
        test_preds = [p for p in race_predictions if p["round"] == test_round]

        win_probs, win_outcomes   = [], []
        top3_probs, top3_outcomes = [], []

        for pred in test_preds:
            key = (test_round, pred["driver_id"])
            if key not in outcome_map:
                continue  # FIX: skip missing entries rather than crashing
            actual_pos = outcome_map[key]
            win_probs.append(pred.get("win_prob", pred.get("win_probability", 0)))
            win_outcomes.append(1 if actual_pos == 1 else 0)
            top3_probs.append(pred.get("top3_prob", pred.get("top3_probability", 0)))
            top3_outcomes.append(1 if actual_pos <= 3 else 0)

        if not win_probs:
            continue

        fold_results.append({
            "test_round":   test_round,
            "n_drivers":    len(win_probs),
            "win_brier":    round(brier_score(win_probs, win_outcomes), 5),
            "win_logloss":  round(log_loss(win_probs, win_outcomes), 5),
            "top3_brier":   round(brier_score(top3_probs, top3_outcomes), 5),
            "top3_logloss": round(log_loss(top3_probs, top3_outcomes), 5),
        })

    return fold_results


def permutation_feature_importance(driver_id: str, circuit_id: str,
                                    n_permutations: int = 20) -> dict:
    from engine.feature_engineering import compute_composite_score
    from config.settings import FEATURE_WEIGHTS
    import random

    baseline = compute_composite_score(driver_id, circuit_id)
    base_score = baseline["composite_score"]
    importance = {}
    for feat in baseline["features"]:
        drops = []
        for _ in range(n_permutations):
            perturbed = dict(baseline["features"])
            perturbed[feat] = random.random()
            new_score = sum(FEATURE_WEIGHTS.get(k, 0.0) * v for k, v in perturbed.items())
            drops.append(base_score - new_score)
        importance[feat] = round(sum(drops) / n_permutations, 6)
    return dict(sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True))


def generate_calibration_report(predicted_probs: List[float], outcomes: List[int],
                                  n_bins: int = 10) -> List[dict]:
    bins = [[] for _ in range(n_bins)]
    for p, o in zip(predicted_probs, outcomes):
        bins[min(int(p * n_bins), n_bins - 1)].append((p, o))
    report = []
    for i, b in enumerate(bins):
        if not b:
            continue
        mean_pred   = sum(p for p, _ in b) / len(b)
        actual_rate = sum(o for _, o in b) / len(b)
        report.append({
            "bin":               f"{i/n_bins:.1f}–{(i+1)/n_bins:.1f}",
            "n":                 len(b),
            "mean_predicted":    round(mean_pred, 4),
            "actual_rate":       round(actual_rate, 4),
            "calibration_error": round(abs(mean_pred - actual_rate), 4),
        })
    return report