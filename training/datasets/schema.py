"""
Canonical historical dataset schema — driver/constructor/circuit/session levels.
This defines the feature store contract; actual rows come from Jolpica/OpenF1/FastF1 backfills.
"""
from dataclasses import dataclass, field
from typing import Optional, List

# Feature schema version — bump when adding/removing features
FEATURE_VERSION = "feature-v8"
DATASET_VERSION = "dataset-v14"

CANONICAL_FEATURES = [
    # driver-level
    "strength","reliability","wet_skill",
    "qualifying_position","qualifying_lap_time","sector_times",
    "starting_position","finishing_position","positions_gained",
    "avg_race_pace","fastest_lap","stint_pace","tyre_compound","tyre_age",
    "pit_stops","pit_duration","dnf","penalties","safety_car_exposure",
    "teammate_delta","recent_form_5","circuit_history","wet_performance",
    # constructor-level
    "constructor_quali_pace","constructor_race_pace","constructor_reliability",
    "constructor_recent_form","circuit_suitability","straight_line_perf",
    "tyre_degradation","pit_performance",
    # circuit-level
    "overtaking_difficulty","avg_speed","drs_zones","corner_count",
    "safety_car_freq","historical_rainfall","air_temp","track_temp",
    "quali_race_correlation",
    # session-level + interactions
    "session_race","session_qualifying","session_practice",
    "weather_dry","weather_mixed","weather_wet","rain_prob","humidity","wind_speed",
    "grid_position","grid_multiplier","grid_weight",
    "strength_x_circuit","wet_skill_x_weather","reliability_x_sc_prob",
]

# Targets for multi-objective training
TARGETS = {
    "win_probability": {"type": "classification", "description": "P(win)"},
    "podium_probability": {"type": "classification", "description": "P(podium)"},
    "points_probability": {"type": "classification", "description": "P(top10)"},
    "dnf_probability": {"type": "classification", "description": "P(DNF)"},
    "expected_finish": {"type": "regression", "description": "E[finish_position]"},
    "qualifying_position": {"type": "ranking", "description": "predicted qual pos"},
    "race_pace": {"type": "regression", "description": "avg race pace"},
}

@dataclass
class DatasetProvenance:
    dataset_version: str = DATASET_VERSION
    feature_version: str = FEATURE_VERSION
    training_cutoff: str = ""
    rows: int = 0
    sources: List[str] = field(default_factory=list)
