"""
Main Prediction Orchestrator.

Ties together feature engineering, probability modelling, and output formatting.
Exposes a clean predict() interface consumed by both the CLI and API.
"""

import random
from dataclasses import dataclass
from typing import Optional, Dict, List
import logging

from data.circuit_data import get_circuit
from engine.probability_model import predict_race
from engine.feature_engineering import compute_all_drivers, compute_feature_contributions


logger = logging.getLogger(__name__)


@dataclass
class PredictionRequest:
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 5000
    seed: Optional[int] = None
    output_format: str = "full"  # "full" | "summary" | "intermediate" | "winner_only"
    include_intermediate_artifacts: bool = False  # Whether to return features/composite scores



@dataclass
class DriverPrediction:
    driver_id: str
    driver_name: str
    team: str
    predicted_position: int
    win_probability: float
    top3_probability: float
    top10_probability: float
    dnf_probability: float
    teammate_beat_prob: float
    composite_score: float
    confidence: str  # "high" | "medium" | "low"
    # Uncertainty metrics
    win_variance: Optional[float] = None
    top3_variance: Optional[float] = None
    top10_variance: Optional[float] = None
    dnf_variance: Optional[float] = None

    @property
    def confidence_label(self) -> str:
        return self.confidence.title()

    def to_dict(self) -> dict:
        result = {
            "driver": self.driver_name,
            "team": self.team,
            "predicted_position": self.predicted_position,
            "win_pct": round(self.win_probability * 100, 1),
            "top3_pct": round(self.top3_probability * 100, 1),
            "top10_pct": round(self.top10_probability * 100, 1),
            "dnf_pct": round(self.dnf_probability * 100, 1),
            "teammate_beat_pct": round(self.teammate_beat_prob * 100, 1),
            "confidence": self.confidence_label,
            "composite_score": self.composite_score,
        }
        
        # Add uncertainty metrics if available
        if self.win_variance is not None:
            result["win_variance"] = round(self.win_variance, 4)
        if self.top3_variance is not None:
            result["top3_variance"] = round(self.top3_variance, 4)
        if self.top10_variance is not None:
            result["top10_variance"] = round(self.top10_variance, 4)
        if self.dnf_variance is not None:
            result["dnf_variance"] = round(self.dnf_variance, 4)
            
        return result


def _assign_confidence(win_prob: float, composite_score: float) -> str:
    """Assign a confidence level based on prediction signal clarity."""
    if win_prob > 0.25 or composite_score > 0.75:
        return "high"
    elif win_prob > 0.05 or composite_score > 0.45:
        return "medium"
    return "low"


def predict(request: PredictionRequest) -> dict:
    """
    Run a full race prediction and return formatted output.
    Implements clear separation between feature computation, probability mapping, 
    Monte Carlo sampling, and post-processing.
    """
    # Set random seed for deterministic runs if provided
    if request.seed is not None:
        random.seed(request.seed)
    
    # Validate circuit exists
    try:
        circuit = get_circuit(request.circuit_id)
    except KeyError:
        logger.error(f"Circuit {request.circuit_id} does not exist")
        raise ValueError(f"Circuit {request.circuit_id} does not exist")
    
    # 1. FEATURE COMPUTATION PHASE
    logger.info(f"Starting feature computation for circuit {request.circuit_id}")
    feature_results = compute_all_drivers(
        circuit_id=request.circuit_id,
        rain_probability=request.rain_probability
    )
    
    # If requested, return intermediate artifacts
    intermediate_artifacts = None
    if request.include_intermediate_artifacts:
        intermediate_artifacts = {
            "feature_contributions": [
                compute_feature_contributions(
                    driver_id=d["driver_id"],
                    circuit_id=request.circuit_id,
                    rain_probability=request.rain_probability
                ) for d in feature_results
            ],
            "composite_scores": {d["driver_id"]: d["composite_score"] for d in feature_results},
        }
    
    # 2. PROBABILITY MAPPING AND MONTE CARLO SAMPLING PHASE
    logger.info(f"Starting probability mapping and Monte Carlo sampling")
    raw = predict_race(
        circuit_id=request.circuit_id,
        rain_probability=request.rain_probability,
        n_simulations=request.n_simulations,
        seed=request.seed,  # Pass seed to ensure deterministic sampling
    )
    
    # 3. POST-PROCESSING INTO OUTPUT FORMAT
    logger.info("Post-processing results into output format")
    predictions = []
    for p in raw["predictions"]:
        # Find corresponding feature result to get composite score
        feature_data = next((fr for fr in feature_results if fr["driver_id"] == p["driver_id"]), None)
        composite_score = feature_data["composite_score"] if feature_data else 0.0
        
        # Extract uncertainty metrics if available in raw results
        uncertainty_metrics = p.get("uncertainty_metrics", {})
        
        dp = DriverPrediction(
            driver_id=p["driver_id"],
            driver_name=p["driver_name"],
            team=p["team"],
            predicted_position=p["predicted_position"],
            win_probability=p["win_probability"],
            top3_probability=p["top3_probability"],
            top10_probability=p["top10_probability"],
            dnf_probability=p["dnf_probability"],
            teammate_beat_prob=p["teammate_beat_prob"],
            composite_score=composite_score,
            confidence=_assign_confidence(p["win_probability"], composite_score),
            win_variance=uncertainty_metrics.get("win_variance"),
            top3_variance=uncertainty_metrics.get("top3_variance"),
            top10_variance=uncertainty_metrics.get("top10_variance"),
            dnf_variance=uncertainty_metrics.get("dnf_variance"),
        )
        predictions.append(dp)

    # ── Summary stats ──────────────────────────────────────────────────────────
    top3 = [p for p in predictions if p.top3_probability > 0.20]
    top_surprise = sorted(
        [p for p in predictions if p.predicted_position > 6 and p.top10_probability > 0.40],
        key=lambda x: x.top10_probability,
        reverse=True,
    )[:3]

    # ── Overall confidence ─────────────────────────────────────────────────────
    # Confidence is dampened by safety car probability and rain
    # circuit may be a pydantic model or dict depending on data layer
    sc_prob = circuit["safety_car_probability"] if isinstance(circuit, dict) else circuit.safety_car_probability
    rain_prob = (request.rain_probability if request.rain_probability is not None else (
        circuit["rain_probability_typical"] if isinstance(circuit, dict) else circuit.rain_probability_typical
    ))
    overall_confidence = max(0.40, 0.90 - (sc_prob * 0.25) - (rain_prob * 0.15))

    # meta fields: support dict or pydantic model
    circuit_name = circuit["name"] if isinstance(circuit, dict) else circuit.name
    circuit_city = circuit["city"] if isinstance(circuit, dict) else circuit.city
    circuit_race_date = circuit["race_date"] if isinstance(circuit, dict) else circuit.race_date
    circuit_sprint_weekend = circuit["sprint_weekend"] if isinstance(circuit, dict) else circuit.sprint_weekend

    result = {
        "meta": {
            "circuit": circuit_name,
            "city": circuit_city,
            "race_date": circuit_race_date,
            "sprint_weekend": circuit_sprint_weekend,
            "safety_car_probability": sc_prob,
            "rain_probability": rain_prob,
            "n_simulations": request.n_simulations,
            "overall_model_confidence": round(overall_confidence, 3),
        },
        "predictions": [p.to_dict() for p in predictions],
        "podium_predictions": [p.driver_name for p in predictions[:3]],
        "likely_top_surprises": [p.driver_name for p in top_surprise],
    }
    
    # Conditionally include raw data based on output format
    if request.output_format == "full":
        result["raw"] = raw
    elif request.output_format == "intermediate":
        result["intermediate_artifacts"] = intermediate_artifacts
    
    return result
