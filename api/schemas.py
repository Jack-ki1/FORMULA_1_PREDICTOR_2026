"""
Pydantic schemas for the F1 Prediction API.

BUG FIX (v2.1): Removed duplicate class definitions that caused unpredictable runtime behavior.
Python silently used the last definition, creating schema contract mismatches.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ── Request schemas ────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    circuit_id: str = Field(..., example="canada")
    rain_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    n_simulations: int = Field(5000, ge=100, le=50000)

    @field_validator("circuit_id")
    @classmethod
    def circuit_id_lowercase(cls, v: str) -> str:
        return v.lower().strip()


class SimulationRequest(BaseModel):
    """POST /simulate — custom simulation with override parameters."""
    race_id: str = Field(..., example="canada")
    rain_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    n_simulations: Optional[int] = Field(5000, ge=100, le=50000)
    seed: Optional[int] = Field(None, description="Seed for deterministic results")
    grid_overrides: Optional[Dict[str, int]] = Field(
        None,
        description="driver_id → grid_position overrides, e.g. {\"verstappen\": 8}",
        example={"verstappen": 8}
    )


# ── Per-driver prediction output ───────────────────────────────────────────────

class DriverPredictionOut(BaseModel):
    """One driver's prediction — used in all prediction responses."""
    driver: str
    team: str
    predicted_position: int
    win_pct: float = Field(ge=0.0, le=100.0)
    top3_pct: float = Field(ge=0.0, le=100.0)
    top10_pct: float = Field(ge=0.0, le=100.0)
    dnf_pct: float = Field(ge=0.0, le=100.0)
    teammate_beat_pct: float = Field(ge=0.0, le=100.0)
    confidence: str


# Keep old name as alias for backward compat
DriverPredictionResponse = DriverPredictionOut


# ── Race metadata ──────────────────────────────────────────────────────────────

class RaceMetaOut(BaseModel):
    circuit: str
    city: str
    race_date: str
    sprint_weekend: bool
    safety_car_probability: float
    rain_probability: float
    n_simulations: int
    overall_model_confidence: float


# ── Full prediction responses ──────────────────────────────────────────────────

class RacePredictionResponse(BaseModel):
    """Full race prediction — GET /predict/{circuit_id}"""
    meta: RaceMetaOut
    predictions: List[DriverPredictionOut]
    podium_predictions: List[str]
    likely_top_surprises: List[str]


class PredictResponse(RacePredictionResponse):
    """Alias kept for backward compatibility."""
    pass


class WinnerPredictionResponse(BaseModel):
    """Win probabilities only — GET /predict/{circuit_id}/winner"""
    circuit: str
    top_5_win_probabilities: List[Dict[str, Any]]


class DNFProbabilityResponse(BaseModel):
    """DNF risk per driver — GET /predict/{circuit_id}/dnf"""
    circuit: str
    dnf_risk: List[Dict[str, Any]]


# ── Standings ──────────────────────────────────────────────────────────────────

class StandingsEntry(BaseModel):
    position: int
    driver: str
    points: int


class ConstructorStandingsEntry(BaseModel):
    position: int
    team: str
    points: int


class StandingsResponse(BaseModel):
    """Combined standings — GET /standings"""
    drivers: List[StandingsEntry]
    constructors: List[ConstructorStandingsEntry]


# ── Circuits ───────────────────────────────────────────────────────────────────

class CircuitSummary(BaseModel):
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
    race_date: str


class CircuitResponse(CircuitSummary):
    """Detailed circuit — GET /circuits/{id}"""
    lap_count: int
    lap_distance_km: float
    total_distance_km: float
    rain_probability_typical: float
    drs_zones: int


class CircuitListResponse(BaseModel):
    """Circuit list — GET /circuits"""
    circuits: List[CircuitSummary]