"""
API Schemas for F1 Prediction Service.

Defines request and response models for the API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class PredictionRequest(BaseModel):
    """Request model for race predictions."""
    circuit_id: str = Field(..., description="ID of the circuit to predict")
    rain_probability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of rain (0-1)")
    n_simulations: int = Field(5000, ge=100, le=50000, description="Number of Monte Carlo simulations")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for deterministic runs")
    output_format: str = Field("full", description="Output format: full, summary, intermediate, winner_only")
    
    @validator('circuit_id')
    def circuit_id_format(cls, v):
        # Validate circuit ID format (alphanumeric with underscores/hyphens)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('circuit_id must be alphanumeric with underscores or hyphens only')
        return v.lower()  # Canonicalize to lowercase


class DriverPredictionResponse(BaseModel):
    """Response model for individual driver predictions."""
    driver: str
    team: str
    predicted_position: int
    win_pct: float = Field(..., ge=0.0, le=100.0)
    top3_pct: float = Field(..., ge=0.0, le=100.0)
    top10_pct: float = Field(..., ge=0.0, le=100.0)
    dnf_pct: float = Field(..., ge=0.0, le=100.0)
    teammate_beat_pct: float = Field(..., ge=0.0, le=100.0)
    confidence: str
    composite_score: float = Field(..., ge=0.0, le=1.0)
    
    # Optional uncertainty metrics
    win_variance: Optional[float] = Field(None, ge=0.0)
    top3_variance: Optional[float] = Field(None, ge=0.0)
    top10_variance: Optional[float] = Field(None, ge=0.0)
    dnf_variance: Optional[float] = Field(None, ge=0.0)


class PredictionMetadata(BaseModel):
    """Metadata for prediction results."""
    circuit: str
    city: str
    race_date: str
    sprint_weekend: bool
    safety_car_probability: float = Field(..., ge=0.0, le=1.0)
    rain_probability: float = Field(..., ge=0.0, le=1.0)
    n_simulations: int
    overall_model_confidence: float = Field(..., ge=0.0, le=1.0)


class PredictionResponse(BaseModel):
    """Full response model for race predictions."""
    meta: PredictionMetadata
    predictions: List[DriverPredictionResponse]
    podium_predictions: List[str]
    likely_top_surprises: List[str]
    
    # Optional fields depending on output format
    raw: Optional[Dict[str, Any]] = None
    intermediate_artifacts: Optional[Dict[str, Any]] = None


class CircuitInfo(BaseModel):
    """Model for circuit information."""
    id: str
    name: str
    location: str
    date: str
    sprint_weekend: bool


class CircuitsResponse(BaseModel):
    """Response model for listing circuits."""
    circuits: List[CircuitInfo]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str