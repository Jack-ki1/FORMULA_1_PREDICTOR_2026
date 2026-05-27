"""
Global Configuration Settings — v2

FIX: grid_position weight raised from 0.04 to 0.12 (now that it's a real computed
feature, not a hardcoded 0.5 placeholder). Corresponding reduction in safety_car_upside
and elo_rating to keep sum = 1.0.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Feature Weights (must sum to 1.0) ─────────────────────────────────────────
# v2 changes:
#   grid_position:    0.04 → 0.12  (now a real feature, not a placeholder)
#   elo_rating:       0.25 → 0.20  (slight reduction to accommodate grid)
#   safety_car_upside: 0.06 → 0.04 (small signal, reduce weight)
# Result: sum still = 1.00

FEATURE_WEIGHTS: dict = {
    "elo_rating":           0.20,   # Dynamic driver skill rating
    "constructor_strength": 0.20,   # Team baseline × circuit history
    "recent_form":          0.15,   # Exponentially-weighted last N races
    "track_type_fit":       0.12,   # Circuit-type match (power/street/technical)
    "grid_position":        0.12,   # Qualifying position (or championship proxy)
    "reliability":          0.10,   # Inverse DNF rate (career + recent blend)
    "weather_adjustment":   0.07,   # Wet skill × rain probability
    "safety_car_upside":    0.04,   # Circuit SC frequency × grid position upside
}

# ── Recency parameters ─────────────────────────────────────────────────────────
RECENCY_DECAY  = 0.92   # λ per race: most recent = 1.0, one race back = 0.92, etc.
RECENCY_WINDOW = 8      # Maximum races to include in form calculation

# ── API settings ───────────────────────────────────────────────────────────────
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
API_HOST  = os.getenv("API_HOST", "0.0.0.0")
API_PORT  = int(os.getenv("API_PORT", "8000"))

# ── Report / output ────────────────────────────────────────────────────────────
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./output")

# ── Validation ─────────────────────────────────────────────────────────────────

def validate_settings():
    errors = []
    weight_sum = sum(FEATURE_WEIGHTS.values())
    if abs(weight_sum - 1.0) > 0.01:
        errors.append(f"Feature weights sum to {weight_sum:.3f}, expected 1.0")
    if not (0 < RECENCY_DECAY <= 1):
        errors.append(f"RECENCY_DECAY must be (0, 1], got {RECENCY_DECAY}")
    if RECENCY_WINDOW <= 0:
        errors.append(f"RECENCY_WINDOW must be positive, got {RECENCY_WINDOW}")
    if errors:
        raise ValueError("Config errors:\n" + "\n".join(errors))

try:
    validate_settings()
except ValueError as e:
    print(f"⚠ Configuration warning: {e}")