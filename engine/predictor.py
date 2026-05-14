"""
Main Prediction Orchestrator.

Ties together feature engineering, probability modelling, and output formatting.
Exposes a clean predict() interface consumed by both the CLI and API.
"""

from dataclasses import dataclass
from typing import Optional

from data.circuit_data import get_circuit
from engine.probability_model import predict_race


@dataclass
class PredictionRequest:
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 5000
    output_format: str = "full"  # "full" | "summary" | "winner_only"


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

    @property
    def confidence_label(self) -> str:
        return self.confidence.title()

    def to_dict(self) -> dict:
        return {
            "driver": self.driver_name,
            "team": self.team,
            "predicted_position": self.predicted_position,
            "win_pct": round(self.win_probability * 100, 1),
            "top3_pct": round(self.top3_probability * 100, 1),
            "top10_pct": round(self.top10_probability * 100, 1),
            "dnf_pct": round(self.dnf_probability * 100, 1),
            "teammate_beat_pct": round(self.teammate_beat_prob * 100, 1),
            "confidence": self.confidence_label,
        }


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
    """
    circuit = get_circuit(request.circuit_id)

    raw = predict_race(
        circuit_id=request.circuit_id,
        rain_probability=request.rain_probability,
        n_simulations=request.n_simulations,
    )

    predictions = []
    for p in raw["predictions"]:
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
            composite_score=p["composite_score"],
            confidence=_assign_confidence(p["win_probability"], p["composite_score"]),
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
    sc_prob = circuit.get("safety_car_probability", 0.5)
    rain_prob = request.rain_probability or circuit.get("rain_probability_typical", 0.2)
    overall_confidence = max(0.40, 0.90 - (sc_prob * 0.25) - (rain_prob * 0.15))

    return {
        "meta": {
            "circuit": circuit["name"],
            "city": circuit["city"],
            "race_date": circuit["race_date"],
            "sprint_weekend": circuit.get("sprint_weekend", False),
            "safety_car_probability": sc_prob,
            "rain_probability": rain_prob,
            "n_simulations": request.n_simulations,
            "overall_model_confidence": round(overall_confidence, 3),
        },
        "predictions": [p.to_dict() for p in predictions],
        "podium_predictions": [p.driver_name for p in predictions[:3]],
        "likely_top_surprises": [p.driver_name for p in top_surprise],
        "raw": raw if request.output_format == "full" else None,
    }
