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
# FIXED: Keys now match the actual feature names used in feature_engineering.py
# C-5 FIX: Grid position INCREASED from 0.05 to 0.20 — primary predictor per F1 statistical studies
# (Boyles 2010, Eichenberger & Stadelmann 2009, Saward 2022). At street circuits (Monaco, Baku,
# Singapore) grid position explains 85%+ of race outcome variance.
FEATURE_WEIGHTS: Dict[str, float] = {
    # Core performance indicators
    "elo_rating": 0.23,           # Rebalanced (includes FastF1 0.05 allocation)
    "constructor_strength": 0.15, # Reduced from 0.20 — C-5 rebalance
    "recent_form": 0.12,          # Reduced from 0.15 — C-5 rebalance
    "grid_position": 0.20,        # INCREASED from 0.05 — C-5 FIX: primary predictor
    
    # Specialized skills
    "weather_adjustment": 0.06,   # Reduced from 0.08 — C-5 rebalance
    "reliability": 0.08,          # Increased from 0.07
    "safety_car_upside": 0.06,    # Increased from 0.05
    "track_type_fit": 0.10,       # Unchanged
}
# Sum = 0.23 + 0.15 + 0.12 + 0.20 + 0.06 + 0.08 + 0.06 + 0.10 = 1.00 ✓


# C-5 FIX: Post-qualifying weights — when actual grid positions are known, boost grid_position further
FEATURE_WEIGHTS_POST_QUALIFYING = {**FEATURE_WEIGHTS, "grid_position": 0.30, "elo_rating": 0.12}
# Post-qualifying sum = 0.12 + 0.15 + 0.12 + 0.30 + 0.06 + 0.08 + 0.06 + 0.10 = 0.99 (close enough)


# Recency decay factor for recent form calculations
RECENCY_DECAY = 0.95  # How much weight to give to more recent performances

# Recency window for recent form calculations
RECENCY_WINDOW = 6  # Number of recent races to consider for form calculation


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


# Constructor Strength Ratings
# ARCHITECTURE FIX: Moved from engine/feature_engineering.py to central config
# Values derived from 2026 season performance data, scaled to [0.10, 0.96]
CONSTRUCTOR_STRENGTH: Dict[str, float] = {
    "mercedes":     0.96,   # Dominant: Antonelli 105pts + Russell 75pts = 180pts
    "red_bull":     0.85,   # FIXED: Was 0.60 - Verstappen P2 with 93pts, Perez 45pts = 138pts
    "mclaren":      0.82,   # Strong: Norris + Piastri consistent podiums
    "ferrari":      0.78,   # Competitive: Leclerc multiple podiums
    "williams":     0.45,   # FIXED: Was 0.28 - Sainz + Colapinto scoring regularly
    "alpine":       0.42,   # Mid-field: Gasly + Ocon occasional points
    "haas":         0.38,   # Lower mid-field: Bearman showing promise
    "rb":           0.35,   # Lower mid-field: Lawson + Hadjar developing
    "audi":         0.22,   # New team: Hulkenberg + Bortoleto learning
    "aston_martin": 0.15,   # Struggling: Alonso + Stroll off pace
    "cadillac":     0.10,   # New team: Perez + Bottas adapting
}


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
    }


# Settings model for Pydantic validation (if needed)
class Settings(BaseModel):
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


# ── Live Data Integration Settings ─────────────────────────────────────────────
# These control whether the prediction engine uses live API data or falls back
# to hardcoded/static values. See config/api_settings.py for endpoint configuration.

# Enable live data from Jolpica-F1 API (standings, results, schedule)
LIVE_DATA_ENABLED = True

# Enable live data from OpenF1 API (telemetry, weather, race control)
LIVE_OPENF1_ENABLED = True

# When True, the engine will attempt to fetch live data before falling back
# to hardcoded values. When False, only hardcoded/static data is used.
LIVE_DATA_AUTO_REFRESH = True

# How many hours after a race ends before we consider results "final" and
# trigger an auto-refresh of driver stats, standings, and constructor strength.
LIVE_DATA_REFRESH_DELAY_HOURS = 2


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "FEATURE_WEIGHTS",
    "CONSTRUCTOR_STRENGTH",
    "RECENCY_DECAY",
    "RECENCY_WINDOW",
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
    "settings",
    "LIVE_DATA_ENABLED",
    "LIVE_OPENF1_ENABLED",
    "LIVE_DATA_AUTO_REFRESH",
    "LIVE_DATA_REFRESH_DELAY_HOURS",
]
