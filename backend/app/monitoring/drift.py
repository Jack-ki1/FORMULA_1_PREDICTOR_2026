"""
Drift detection — prediction drift, feature drift, performance drift.
"""
import numpy as np
from typing import Dict, Any, List

def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index."""
    exp_hist, _ = np.histogram(expected, bins=bins)
    act_hist, _ = np.histogram(actual, bins=bins)
    exp_hist = exp_hist + 0.5
    act_hist = act_hist + 0.5
    exp_pct = exp_hist / exp_hist.sum()
    act_pct = act_hist / act_hist.sum()
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))

def detect_drift(baseline_probs: Dict[str,float], current_probs: Dict[str,float], threshold: float = 0.25) -> Dict[str,Any]:
    codes = sorted(set(baseline_probs) & set(current_probs))
    if not codes:
        return {"drift": False, "psi": 0.0}
    b = np.array([baseline_probs[c] for c in codes])
    c = np.array([current_probs[c] for c in codes])
    score = psi(b, c)
    return {"drift": score > threshold, "psi": round(score,4), "threshold": threshold, "warning": "Prediction model performance has degraded" if score>threshold else None}
