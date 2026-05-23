"""
Pydantic schemas for the F1 Prediction API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    circuit_id: str = Field(..., example="canada", description="Circuit ID (e.g. 'canada', 'monaco')")
    rain_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override rain probability [0–1]")
    n_simulations: int = Field(5000, ge=100, le=50000, description="Monte Carlo simulation runs")

    @field_validator("circuit_id")
    @classmethod
    def circuit_id_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class DriverPredictionResponse(BaseModel):
    driver: str
    team: str
    predicted_position: int
    win_pct: float
    top3_pct: float
    top10_pct: float
    dnf_pct: float
    teammate_beat_pct: float
    confidence: str


class PredictResponse(BaseModel):
    circuit: str
    city: str
    race_date: str
    sprint_weekend: bool
    safety_car_probability: float
    rain_probability: float
    overall_model_confidence: float
    n_simulations: int
    podium_predictions: List[str]
    likely_top_surprises: List[str]
    predictions: List[DriverPredictionResponse]


class StandingsEntry(BaseModel):
    position: int
    driver: str
    points: int


class ConstructorStandingsEntry(BaseModel):
    position: int
    team: str
    points: int


class CircuitResponse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    circuit_type: List[str]
    safety_car_probability: float
    overtaking_difficulty: int
    power_unit_demand: float
    brake_demand: float
    sprint_weekend: bool
