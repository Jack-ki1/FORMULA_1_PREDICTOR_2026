"""
Pydantic Schemas for F1 Prediction API v3.0.

Request and response models for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


# ── Prediction Request/Response ────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    circuit_id: str
    rain_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override rain probability (0.0-1.0)")
    n_simulations: int = Field(10000, ge=100, le=500000, description="Number of Monte Carlo simulations")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    grid_overrides: Optional[Dict[str, int]] = Field(None, description="Override grid positions: {driver_id: position}")


class PredictionResponse(BaseModel):
    meta: Dict
    predictions: List[Dict]
    podium_predictions: List[str]
    likely_top_surprises: Optional[List[str]] = None


# ── Race Meta ──────────────────────────────────────────────────────────────────

class RaceMetaOut(BaseModel):
    circuit: str
    city: str
    race_date: str
    sprint_weekend: bool
    safety_car_probability: float
    rain_probability: float
    overall_model_confidence: float
    n_simulations: int


class DriverPredictionOut(BaseModel):
    driver: str
    team: str
    predicted_position: int
    win_pct: float
    top3_pct: float
    top10_pct: float
    dnf_pct: float
    teammate_beat_pct: float
    confidence: str


# ── Full Race Prediction Response ──────────────────────────────────────────────

class RacePredictionResponse(BaseModel):
    meta: RaceMetaOut
    predictions: List[DriverPredictionOut]
    podium_predictions: List[str]
    likely_top_surprises: Optional[List[str]] = None


# ── Winner Prediction ──────────────────────────────────────────────────────────

class WinnerPredictionResponse(BaseModel):
    winners: List[Dict[str, float]]


# ── DNF Probability ────────────────────────────────────────────────────────────

class DNFProbabilityResponse(BaseModel):
    dnf_probabilities: List[Dict]


# ── Head-to-Head Comparison ────────────────────────────────────────────────────

class H2HComparisonResponse(BaseModel):
    driver1: str
    driver2: str
    driver1_finishes_ahead_pct: float
    driver2_finishes_ahead_pct: float
    driver1_avg_position: float
    driver2_avg_position: float
    notes: str


# ── Standings ──────────────────────────────────────────────────────────────────

class StandingsEntry(BaseModel):
    driver: str
    position: int
    points: float
    wins: int
    podiums: int


class ConstructorStandingsEntry(BaseModel):
    constructor: str
    position: int
    points: float
    wins: int
    podiums: int


class StandingsResponse(BaseModel):
    driver_standings: List[StandingsEntry]
    constructor_standings: List[ConstructorStandingsEntry]


# ── Circuits ───────────────────────────────────────────────────────────────────

class CircuitSummary(BaseModel):
    id: str
    name: str
    round: int
    date: str
    sprint: bool
    safety_car_probability: float


class CircuitResponse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    lap_record: str
    number_of_laps: int
    lap_distance: float
    race_distance: float
    circuit_type: str
    overtaking_difficulty: float
    safety_car_probability: float


class CircuitListResponse(BaseModel):
    circuits: List[CircuitSummary]


# ── Custom Simulation ──────────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 10000
    seed: Optional[int] = None
    grid_overrides: Optional[Dict[str, int]] = None


# ── Championship Simulator ─────────────────────────────────────────────────────

class ChampionshipSimResponse(BaseModel):
    driver_championship: Dict[str, float]
    constructor_championship: Dict[str, float]
    remaining_races: int
    n_simulations: int


# ── Constructor Predictions ────────────────────────────────────────────────────

class ConstructorPredictionResponse(BaseModel):
    constructors: List[Dict]
    meta: Dict


# ── Accuracy Stats ─────────────────────────────────────────────────────────────

class AccuracyStatsResponse(BaseModel):
    total_predictions: int
    evaluated_predictions: int
    avg_brier_score: Optional[float] = None
    calibration: Optional[str] = None


# ── H2H Request (for routes_v3) ────────────────────────────────────────────────

class H2HRequest(BaseModel):
    driver1: str
    driver2: str
    circuit_id: str
    rain_probability: Optional[float] = None
    n_simulations: int = 10000
