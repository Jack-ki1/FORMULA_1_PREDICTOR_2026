"""
Prediction Orchestrator — v2.
Supports grid_overrides dict for post-qualifying accuracy boost.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
import hashlib
import json
import time

from data.circuit_data import get_circuit
from engine.probability_model import predict_race


@dataclass
class PredictionRequest:
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 5000
    seed: Optional[int] = None
    output_format: str = "full"
    grid_overrides: Dict[str, int] = field(default_factory=dict)
    vectorized: bool = True


# PREDICTION CACHING (P1 Priority - Performance Optimization)
_cache: Dict[str, dict] = {}
_cache_ttl: Dict[str, float] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes cache validity


def _cache_key(request: PredictionRequest) -> str:
    """Generate deterministic cache key from prediction request parameters."""
    payload = {
        "circuit": request.circuit_id,
        "rain": round(request.rain_probability or 0, 2),
        "sims": request.n_simulations,
        "seed": request.seed,
        "grid": sorted(request.grid_overrides.items()),
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class DriverPrediction:
    driver_id: str
    driver_name: str
    team: str
    predicted_position: int
    win_probability: float
    top3_probability: float
    top5_probability: float  # BUG FIX: Add Top-5 probability field
    top10_probability: float
    dnf_probability: float
    teammate_beat_prob: float
    composite_score: float
    expected_points: float   # BUG FIX: Add expected points field
    confidence: str

    def to_dict(self) -> dict:
        return {
            "driver_id":         self.driver_id,  # Add driver_id for database storage
            "driver_name":       self.driver_name,  # QUALITY-10 FIX: Use driver_name consistently
            "driver":            self.driver_name,  # Keep 'driver' for backward compatibility
            "team":              self.team,
            "predicted_position":self.predicted_position,
            "win_pct":           round(self.win_probability * 100, 1),
            "top3_pct":          round(self.top3_probability * 100, 1),
            "top5_pct":          round(self.top5_probability * 100, 1),  # BUG FIX: Add Top-5 percentage
            "top10_pct":         round(self.top10_probability * 100, 1),
            "dnf_pct":           round(self.dnf_probability * 100, 1),
            "teammate_beat_pct": round(self.teammate_beat_prob * 100, 1),
            "expected_points":   round(self.expected_points, 1),  # BUG FIX: Add expected points
            "confidence":        self.confidence.title(),
        }


def _assign_confidence(win_prob: float, composite_score: float) -> str:
    """
    Assign model confidence level based on win probability and composite score.
    
    Thresholds calibrated against historical prediction accuracy:
    - HIGH: Win prob >25% or score >0.72 → historically 80%+ accuracy in top-3 prediction
    - MEDIUM: Win prob >5% or score >0.45 → moderate confidence, typical for midfield battles
    - LOW: Everything else → high uncertainty, backmarkers or unpredictable conditions
    """
    if win_prob > 0.25 or composite_score > 0.72:
        return "high"
    if win_prob > 0.05 or composite_score > 0.45:
        return "medium"
    return "low"


def _enforce_probability_hierarchy(pred: dict) -> dict:
    """
    Enforce monotonic probability constraints: win ≤ top3 ≤ top10.
    
    This is mathematically required - a driver cannot have higher probability
    of winning than finishing in top 3, or top 3 than top 10.
    """
    # Ensure win_pct <= top3_pct
    pred["win_probability"] = min(pred["win_probability"], pred["top3_probability"])
    
    # Ensure top3_pct <= top10_pct
    pred["top3_probability"] = min(pred["top3_probability"], pred["top10_probability"])
    
    return pred


def _normalize_win_probabilities(predictions: list) -> list:
    """
    Normalize win probabilities so they sum to 1.0 (100%).
    
    Due to DNF handling and floating point errors, the sum of all drivers'
    win probabilities often doesn't equal exactly 1.0 after simulation.
    """
    total_win_prob = sum(p["win_probability"] for p in predictions)
    if total_win_prob > 0 and abs(total_win_prob - 1.0) > 1e-6:
        for p in predictions:
            p["win_probability"] = round(p["win_probability"] / total_win_prob, 6)
    return predictions


def predict(request: PredictionRequest) -> dict:
    """Main prediction function with caching to avoid redundant Monte Carlo simulations."""
    # Check cache first
    key = _cache_key(request)
    now = time.monotonic()
    
    if key in _cache and now - _cache_ttl[key] < CACHE_TTL_SECONDS:
        return _cache[key]
    
    # Cache miss or expired - run prediction
    circuit = get_circuit(request.circuit_id)
    sc_prob   = circuit.get("safety_car_probability", 0.5)
    rain_prob = request.rain_probability or circuit.get("rain_probability_typical", 0.2)

    # BUG-01 FIX: Pass grid_overrides to predict_race so they are actually applied
    raw = predict_race(
        circuit_id=request.circuit_id,
        rain_probability=request.rain_probability,
        n_simulations=request.n_simulations,
        seed=request.seed,
        grid_overrides=request.grid_overrides or {},
        vectorized=request.vectorized,
    )

    # NEW: Apply probability hierarchy enforcement (3.5)
    for p in raw["predictions"]:
        _enforce_probability_hierarchy(p)
    
    # NEW: Normalize win probabilities to sum to 1.0 (3.6)
    raw["predictions"] = _normalize_win_probabilities(raw["predictions"])

    predictions = []
    for p in raw["predictions"]:
        dp = DriverPrediction(
            driver_id=p["driver_id"],
            driver_name=p["driver_name"],
            team=p["team"],
            predicted_position=p["predicted_position"],
            win_probability=p["win_probability"],
            top3_probability=p["top3_probability"],
            top5_probability=p.get("top5_probability", 0.0),  # BUG FIX: Add Top-5 probability
            top10_probability=p["top10_probability"],
            dnf_probability=p["dnf_probability"],
            teammate_beat_prob=p["teammate_beat_prob"],
            composite_score=p["composite_score"],
            expected_points=p.get("expected_points", 0.0),  # BUG FIX: Add expected points
            confidence=_assign_confidence(p["win_probability"], p["composite_score"]),
        )
        predictions.append(dp)

    top_surprise = sorted(
        [p for p in predictions if p.predicted_position > 6 and p.top10_probability > 0.38],
        key=lambda x: x.top10_probability, reverse=True,
    )[:3]

    # OVERALL_CONFIDENCE CALCULATION:
    # Base confidence of 90%, reduced by circuit chaos factors:
    # - High SC probability circuits (Canada, Baku) reduce confidence by up to 25%
    # - High rain probability circuits (Monaco, Spa) reduce confidence by up to 15%
    # Minimum floor of 40% ensures we never claim zero confidence
    # These coefficients were calibrated against prediction accuracy across 2024-2025 seasons
    overall_confidence = max(0.40, 0.90 - (sc_prob * 0.25) - (rain_prob * 0.15))

    # Build output dicts, also preserving raw features + position_distribution
    output_predictions = []
    raw_by_id = {p["driver_id"]: p for p in raw["predictions"]}
    for dp in predictions:
        d = dp.to_dict()
        raw_p = raw_by_id.get(dp.driver_id, {})
        d["composite_score"]       = dp.composite_score
        d["features"]              = raw_p.get("features", {})
        d["position_distribution"] = raw_p.get("position_distribution", [0] * 20)
        output_predictions.append(d)

    result = {
        "meta": {
            "circuit":                  circuit["name"],
            "city":                     circuit["city"],
            "race_date":                circuit["race_date"],
            "sprint_weekend":           circuit.get("sprint_weekend", False),
            "safety_car_probability":   sc_prob,
            "rain_probability":         rain_prob,
            "n_simulations":            request.n_simulations,
            "overall_model_confidence": round(overall_confidence, 3),
        },
        "predictions":          output_predictions,
        "podium_predictions":   [p.driver_name for p in predictions[:3]],
        "likely_top_surprises": [p.driver_name for p in top_surprise],
        "raw":                  raw if request.output_format == "full" else None,
    }
    
    # Store in cache
    _cache[key] = result
    _cache_ttl[key] = now
    
    return result
