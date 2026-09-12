"""Pydantic schemas for prediction endpoint — explicit contract."""
try:
    from pydantic import BaseModel, Field, field_validator
    HAS_PYDANTIC=True
except ImportError:
    HAS_PYDANTIC=False
    BaseModel=object

if HAS_PYDANTIC:
    from typing import Optional, Dict, Any
    class PredictionRequest(BaseModel):
        race_id: str = Field(..., description="Race identifier e.g. 'au'")
        session_type: str = Field(default="race", description="race|qualifying|practice")
        sub_session: Optional[str] = Field(default=None)
        weather: str = Field(default="dry")
        grid_positions: Optional[Dict[str,int]] = None
        feature_weights: Optional[Dict[str,float]] = None
        simulation_count: int = Field(default=10000, ge=100, le=100000)
        ai_mode: str = Field(default="normal")
        ai_model: str = Field(default="gemini-2.0-flash-exp")
        ai_api_key: str = Field(default="")
        ai_weight: float = Field(default=0.3, ge=0, le=1)
        ai_temperature: float = Field(default=0.7, ge=0, le=2)
        @field_validator("session_type")
        @classmethod
        def validate_session(cls,v):
            if v.lower() not in ("race","qualifying","practice"):
                raise ValueError("session_type must be race|qualifying|practice")
            return v.lower()
        @field_validator("weather")
        @classmethod
        def validate_weather(cls,v):
            if v.lower() not in ("dry","mixed","wet"):
                raise ValueError("weather must be dry|mixed|wet")
            return v.lower()
    class PredictionResponse(BaseModel):
        race_id: str
        session_type: str
        predictions: Dict[str, Any]
        winner_probabilities: Dict[str,float]
        confidence_intervals: Dict[str, Any]
        grid_positions: Dict[str,int]
        model_drift_score: float | None = None
        timestamp: str
        status: str
else:
    # fallback stubs
    PredictionRequest = dict
    PredictionResponse = dict
