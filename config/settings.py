"""
Global Configuration Settings.

Structured configuration for the F1 prediction system with per-module sections.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ── Logging Setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

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
    # NOTE: grid_position is a placeholder and should be handled separately when grid is known
    # It is intentionally excluded from automatic weighting calculations
}

# Auto-normalize feature weights (excluding placeholders) so they sum to 1.0.
# This keeps validate_settings() stable even if weights are edited later.
_active_weight_sum = sum(v for k, v in FEATURE_WEIGHTS.items() if k != "grid_position")
if _active_weight_sum and abs(_active_weight_sum - 1.0) > 1e-9:
    for _k in list(FEATURE_WEIGHTS.keys()):
        if _k == "grid_position":
            continue
        FEATURE_WEIGHTS[_k] = FEATURE_WEIGHTS[_k] / _active_weight_sum



@dataclass
class FeatureEngineeringConfig:

    """Configuration for feature engineering module."""
    # Time decay parameters
    recency_decay: float = 0.92      # How much to discount each previous race (most recent = 1.0)
    recency_window: int = 8          # Number of recent races to consider in form calculations
    
    # Normalization baselines
    wet_skill_midpoint: float = 0.75  # Midpoint for wet skill normalization
    weather_effect_multiplier: float = 4.0  # Multiplier for weather impact
    sc_upside_max: float = 0.8       # Maximum safety car upside
    
    # Scaling factors
    weather_scaling_factor: float = 4.0
    sc_upside_scaling_factor: float = 1.0
    dnf_exp_factor_base: float = 0.05
    
    # Named constants for magic numbers
    elo_field_size_min: float = 1460.0
    elo_field_size_max: float = 1645.0
    track_fit_range_min: float = 0.85
    track_fit_range_max: float = 1.25  # Changed from 1.20 to allow more flexibility
    base_reliability: float = 0.7
    typical_field_size: int = 20


@dataclass
class ProbabilityModelConfig:
    """Configuration for probability modeling."""
    # Calibration parameters
    platt_a_win: float = 1.12
    platt_b_win: float = -0.08
    platt_a_top3: float = 1.05
    platt_b_top3: float = -0.04
    platt_a_top10: float = 1.02
    platt_b_top10: float = -0.03
    platt_a_dnf: float = 0.95
    platt_b_dnf: float = 0.02
    
    # Simulation parameters
    default_simulation_runs: int = 5000
    min_simulation_runs: int = 100
    max_simulation_runs: int = 50000
    temperature_softmax: float = 0.25
    
    # Probability thresholds
    min_probability: float = 1e-6
    max_probability: float = 1.0 - 1e-6


@dataclass
class EngineConfig:
    """Overall engine configuration."""
    # Seed control for deterministic runs
    default_seed: Optional[int] = None
    
    # Feature engineering config
    feature_eng: FeatureEngineeringConfig = None
    
    # Probability model config
    prob_model: ProbabilityModelConfig = None
    
    # Validation bounds
    weight_normalization_tolerance: float = 0.01
    simulation_count_bounds: tuple = (100, 50000)
    
    def __post_init__(self):
        if self.feature_eng is None:
            self.feature_eng = FeatureEngineeringConfig()
        if self.prob_model is None:
            self.prob_model = ProbabilityModelConfig()
        
        # Override defaults with environment variables if present
        seed_str = os.getenv("PREDICTION_SEED")
        if seed_str is not None:
            try:
                self.default_seed = int(seed_str)
            except ValueError:
                logger.warning(f"Invalid seed value from environment: {seed_str}, using None")


@dataclass
class ApiConfig:
    """API-specific configuration."""
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour default cache
    
    def __post_init__(self):
        self.debug = os.getenv("API_DEBUG", str(self.debug)).lower() == "true"
        self.host = os.getenv("API_HOST", self.host)
        try:
            self.port = int(os.getenv("API_PORT", str(self.port)))
        except ValueError:
            logger.warning(f"Invalid port from environment, using default {self.port}")
        
        # Validate API settings
        if not (1 <= self.port <= 65535):
            logger.error(f"Port {self.port} is out of valid range (1-65535), resetting to default")
            self.port = 8000


@dataclass
class ReportConfig:
    """Report generation configuration."""
    output_dir: str = "./reports/output"
    template_dir: str = "./reports/templates"
    version_tag: str = "v1.0"
    
    def __post_init__(self):
        self.output_dir = os.getenv("REPORT_OUTPUT_DIR", self.output_dir)
        self.template_dir = os.getenv("REPORT_TEMPLATE_DIR", self.template_dir)


# ── Initialize Configuration ───────────────────────────────────────────────────

ENGINE_CONFIG = EngineConfig()
API_CONFIG = ApiConfig()
REPORT_CONFIG = ReportConfig()

# Backwards-compatible module-level exports (used by existing imports).
RECENCY_DECAY = ENGINE_CONFIG.feature_eng.recency_decay
RECENCY_WINDOW = ENGINE_CONFIG.feature_eng.recency_window

# ── Validation ─────────────────────────────────────────────────────────────────


def validate_settings():
    """Validate that all settings are properly configured."""
    errors = []

    # Check feature weights sum to approximately 1.0 (excluding grid_position placeholder)
    active_weights = {k: v for k, v in FEATURE_WEIGHTS.items() if k != "grid_position"}
    weight_sum = sum(active_weights.values())
    if abs(weight_sum - 1.0) > ENGINE_CONFIG.weight_normalization_tolerance:
        errors.append(f"Active feature weights should sum to 1.0, got {weight_sum}")

    if ENGINE_CONFIG.feature_eng.recency_decay <= 0 or ENGINE_CONFIG.feature_eng.recency_decay > 1:
        errors.append(f"RECENCY_DECAY must be between 0 and 1, got {ENGINE_CONFIG.feature_eng.recency_decay}")

    if ENGINE_CONFIG.feature_eng.recency_window <= 0:
        errors.append(f"RECENCY_WINDOW must be positive, got {ENGINE_CONFIG.feature_eng.recency_window}")

    # Validate simulation counts
    sim_runs = ENGINE_CONFIG.prob_model.default_simulation_runs
    min_runs, max_runs = ENGINE_CONFIG.simulation_count_bounds
    if sim_runs < min_runs or sim_runs > max_runs:
        errors.append(f"Simulation count {sim_runs} out of bounds [{min_runs}, {max_runs}]")

    # Validate API settings
    if not (1 <= API_CONFIG.port <= 65535):
        errors.append(f"API port {API_CONFIG.port} is out of valid range (1-65535)")

    if errors:
        error_msg = "Configuration errors found:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)


# Validate settings on import
try:
    validate_settings()
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    raise