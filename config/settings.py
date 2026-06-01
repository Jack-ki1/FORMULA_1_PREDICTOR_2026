"""
Configuration Settings for F1 Prediction System v3.0.

Contains all configurable parameters for the prediction engine including:
  - Feature weights for the composite score calculation
  - API settings and defaults
  - Simulation parameters
  - Model configuration
"""

from typing import Dict, Any
from pydantic import BaseModel
import os


# Feature weights - these determine how much each factor influences predictions
# They should sum to approximately 1.0 (though small deviations are OK)
FEATURE_WEIGHTS: Dict[str, float] = {
    # Core performance indicators
    "elo_rating":           0.25,   # Overall driver skill rating (matches engine key)
    "constructor_strength": 0.20,   # Team performance level (matches engine key)
    "recent_form":          0.15,   # Performance in last 6 races
    "grid_position":        0.15,   # Starting position advantage
    
    # Specialized skills
    "weather_adjustment":   0.08,   # Wet weather driving ability (matches engine key)
    "reliability":          0.07,   # Driver reliability (matches engine key)
    "safety_car_upside":    0.05,   # Ability to capitalize on SC situations (matches engine key)
    "track_type_fit":       0.05,   # Suitability to specific circuit characteristics (matches engine key)
}


# Recency decay factor for recent form calculations
RECENCY_DECAY = 0.95  # How much weight to give to more recent performances

# Recency window for recent form calculations
RECENCY_WINDOW = 6  # Number of recent races to consider for form calculation


# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # SECURITY FIX: Default to localhost
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# Simulation Parameters
DEFAULT_N_SIMULATIONS = 5000
MAX_SIMULATIONS = 50000
MIN_SIMULATIONS = 100


# Model Configuration
DEFAULT_RAIN_PROBABILITY = 0.10
DEFAULT_SAFETY_CAR_PROBABILITY = 0.35
DNF_BASELINE_RATE = 0.08  # Base DNF rate before adjustments


# Confidence Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.25  # Win prob above this = high confidence
MEDIUM_CONFIDENCE_THRESHOLD = 0.10  # Win prob above this = medium confidence


# Validation function
def validate_settings() -> Dict[str, Any]:
    """
    Validate configuration settings and return any issues.
    
    Returns:
        Dictionary with 'valid' (bool) and 'errors' (list) keys
    """
    errors = []
    
    # Check feature weights sum
    weight_sum = sum(FEATURE_WEIGHTS.values())
    if abs(weight_sum - 1.0) > 0.02:  # Allow 2% tolerance
        errors.append(f"Feature weights sum to {weight_sum:.3f}, expected ~1.0")
    
    # Check individual weights are positive
    for name, weight in FEATURE_WEIGHTS.items():
        if weight < 0:
            errors.append(f"Feature weight '{name}' is negative: {weight}")
    
    # Check simulation bounds
    if MIN_SIMULATIONS < 10:
        errors.append(f"MIN_SIMULATIONS too low: {MIN_SIMULATIONS}")
    if MAX_SIMULATIONS > 100000:
        errors.append(f"MAX_SIMULATIONS too high: {MAX_SIMULATIONS}")
    if DEFAULT_N_SIMULATIONS < MIN_SIMULATIONS or DEFAULT_N_SIMULATIONS > MAX_SIMULATIONS:
        errors.append(f"DEFAULT_N_SIMULATIONS {DEFAULT_N_SIMULATIONS} not in range [{MIN_SIMULATIONS}, {MAX_SIMULATIONS}]")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "weight_sum": weight_sum,
        "config": {
            "api_host": API_HOST,
            "api_port": API_PORT,
            "debug": DEBUG,
            "default_simulations": DEFAULT_N_SIMULATIONS,
        }
    }


# Settings model for Pydantic validation (if needed by API)
class Settings(BaseModel):
    api_host: str = API_HOST
    api_port: int = API_PORT
    debug: bool = DEBUG
    feature_weights: Dict[str, float] = FEATURE_WEIGHTS
    recency_decay: float = RECENCY_DECAY
    recency_window: int = RECENCY_WINDOW
    default_simulations: int = DEFAULT_N_SIMULATIONS
    max_simulations: int = MAX_SIMULATIONS
    min_simulations: int = MIN_SIMULATIONS
    default_rain_probability: float = DEFAULT_RAIN_PROBABILITY
    default_safety_car_probability: float = DEFAULT_SAFETY_CAR_PROBABILITY
    dnf_baseline_rate: float = DNF_BASELINE_RATE
    high_confidence_threshold: float = HIGH_CONFIDENCE_THRESHOLD
    medium_confidence_threshold: float = MEDIUM_CONFIDENCE_THRESHOLD

    class Config:
        case_sensitive = False


# Initialize settings instance
settings = Settings()


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "FEATURE_WEIGHTS",
    "RECENCY_DECAY",
    "RECENCY_WINDOW",
    "API_HOST", 
    "API_PORT", 
    "DEBUG",
    "DEFAULT_N_SIMULATIONS",
    "MAX_SIMULATIONS",
    "MIN_SIMULATIONS",
    "DEFAULT_RAIN_PROBABILITY",
    "DEFAULT_SAFETY_CAR_PROBABILITY",
    "DNF_BASELINE_RATE",
    "HIGH_CONFIDENCE_THRESHOLD",
    "MEDIUM_CONFIDENCE_THRESHOLD",
    "validate_settings",
    "Settings",
    "settings"
]