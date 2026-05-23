"""
Global Configuration Settings.

All constants and weights used across the prediction system.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Feature Weights ────────────────────────────────────────────────────────────

FEATURE_WEIGHTS: dict = {
    # Core performance indicators
    "elo_rating":           0.25,
    "constructor_strength": 0.20,
    "recent_form":          0.15,
    "track_type_fit":       0.12,

    # Risk factors
    "reliability":          0.10,
    "weather_adjustment":   0.08,

    # Race-specific factors
    "safety_car_upside":    0.06,
    "grid_position":        0.04,  # Placeholder; will be replaced when grid is known
}

# ── Time Decay Parameters ──────────────────────────────────────────────────────

RECENCY_DECAY = 0.92      # How much to discount each previous race (most recent = 1.0)
RECENCY_WINDOW = 8        # Number of recent races to consider in form calculations

# ── API Settings ───────────────────────────────────────────────────────────────

API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── Report Settings ────────────────────────────────────────────────────────────

REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./reports/output")

# ── Validation ─────────────────────────────────────────────────────────────────


def validate_settings():
    """Validate that all settings are properly configured."""
    errors = []

    # Check feature weights sum to approximately 1.0
    weight_sum = sum(FEATURE_WEIGHTS.values())
    if abs(weight_sum - 1.0) > 0.01:
        errors.append(f"Feature weights should sum to 1.0, got {weight_sum}")

    if RECENCY_DECAY <= 0 or RECENCY_DECAY > 1:
        errors.append(f"RECENCY_DECAY must be between 0 and 1, got {RECENCY_DECAY}")

    if RECENCY_WINDOW <= 0:
        errors.append(f"RECENCY_WINDOW must be positive, got {RECENCY_WINDOW}")

    if errors:
        raise ValueError("Configuration errors found:\n" + "\n".join(errors))


# Validate settings on import
try:
    validate_settings()
except ValueError as e:
    print(f"Configuration warning: {e}")

