"""
F1 Circuit Database — 2026 Season

Schema-validated circuit data with explicit typing and validation.
Version 1.0 - 2025-05-13
"""

from typing import Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field, validator
import logging
import re

logger = logging.getLogger(__name__)

# ── Schema Definition ──────────────────────────────────────────────────────────

class CircuitData(BaseModel):
    id: str
    name: str
    city: str
    country: str
    round_2026: int
    race_date: str  # Format: YYYY-MM-DD
    sprint_weekend: bool
    circuit_type: List[str]
    lap_count: int
    lap_distance_km: float
    total_distance_km: float
    safety_car_probability: float = Field(ge=0.0, le=1.0)
    overtaking_difficulty: int = Field(ge=1, le=10)
    power_unit_demand: float = Field(ge=0.0, le=10.0)
    brake_demand: float = Field(ge=0.0, le=10.0)
    tire_deg_rate: float = Field(ge=0.0, le=10.0)
    active_aero_demand: float = Field(ge=0.0, le=10.0)
    rain_probability_typical: float = Field(ge=0.0, le=1.0)
    wall_crash_probability_per_lap: float = Field(ge=0.0, le=1.0)
    drs_zones: int
    overtake_zones: Optional[List[str]] = []
    key_corners: Optional[List[str]] = []
    optimal_setup: Optional[str] = None
    team_historical_wins_since_2010: Optional[Dict[str, int]] = {}
    driver_historical_wins: Optional[Dict[str, int]] = {}
    notes: Optional[str] = None

    @validator('circuit_type')
    def circuit_type_valid(cls, v):
        valid_types = {"power_unit", "street", "balanced", "high_downforce", "technical"}
        for ct in v:
            if ct not in valid_types:
                raise ValueError(f'Circuit type "{ct}" not in valid types: {valid_types}')
        return v

    @validator('race_date')
    def date_format_valid(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError(f'Date format invalid for "{v}", expected YYYY-MM-DD')
        return v

    @validator('safety_car_probability', 'rain_probability_typical', 'wall_crash_probability_per_lap')
    def probability_in_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError(f'Probability value {v} not in range [0.0, 1.0]')
        return v

# ── Circuit Data with Schema ───────────────────────────────────────────────────

CIRCUIT_DATA_RAW: Dict[str, dict] = {


    "canada": {
        "id": "canada",
        "name": "Circuit Gilles-Villeneuve",
        "city": "Montreal",
        "country": "Canada",
        "round_2026": 5,
        "race_date": "2026-05-24",
        "sprint_weekend": True,
        "circuit_type": ["power_unit", "street"],
        "lap_count": 70,
        "lap_distance_km": 4.361,
        "total_distance_km": 305.27,
        "safety_car_probability": 0.82,        # Highest on calendar
        "overtaking_difficulty": 4,             # Relatively easy (long straight)
        "power_unit_demand": 8.5,
        "brake_demand": 8.5,
        "tire_deg_rate": 6.0,
        "active_aero_demand": 8.0,
        "rain_probability_typical": 0.35,       # Late May Montreal
        "wall_crash_probability_per_lap": 0.004, # Wall of Champions effect
        "drs_zones": 2,
        "overtake_zones": ["Pit straight", "After Hairpin"],
        "key_corners": ["Turn 1–2 chicane", "Turn 10 Hairpin", "Wall of Champions"],
        "optimal_setup": "low_drag",
        "team_historical_wins_since_2010": {
            "mercedes": 10,
            "red_bull": 8,
            "ferrari": 4,
            "mclaren": 2,
            "renault": 1,
            "williams": 0,
        },
        "driver_historical_wins": {
            "hamilton": 7,
            "verstappen": 5,
            "vettel": 3,
            "alonso": 2,
            "button": 2,
        },
        "notes": "Stop-start island circuit. Wall of Champions catches title-fight leaders regularly.",
    },
    "australia": {
        "id": "australia",
        "name": "Albert Park Circuit",
        "city": "Melbourne",
        "country": "Australia",
        "round_2026": 1,
        "race_date": "2026-03-08",
        "sprint_weekend": False,
        "circuit_type": ["street", "balanced"],
        "lap_count": 58,
        "lap_distance_km": 5.303,
        "total_distance_km": 307.574,
        "safety_car_probability": 0.68,
        "overtaking_difficulty": 6,
        "power_unit_demand": 6.5,
        "brake_demand": 7.0,
        "tire_deg_rate": 5.5,
        "active_aero_demand": 7.0,
        "rain_probability_typical": 0.25,
        "wall_crash_probability_per_lap": 0.003,
        "drs_zones": 3,
        "team_historical_wins_since_2010": {
            "mercedes": 7,
            "red_bull": 5,
            "ferrari": 3,
            "mclaren": 1,
        },
    },
    "china": {
        "id": "china",
        "name": "Shanghai International Circuit",
        "city": "Shanghai",
        "country": "China",
        "round_2026": 2,
        "race_date": "2026-03-15",
        "sprint_weekend": True,
        "circuit_type": ["balanced", "high_downforce"],
        "lap_count": 56,
        "lap_distance_km": 5.451,
        "total_distance_km": 305.066,
        "safety_car_probability": 0.55,
        "overtaking_difficulty": 5,
        "power_unit_demand": 7.0,
        "brake_demand": 6.5,
        "tire_deg_rate": 6.0,
        "active_aero_demand": 7.5,
        "rain_probability_typical": 0.40,
        "wall_crash_probability_per_lap": 0.002,
        "drs_zones": 1,
        "overtake_zones": ["Main straight"],
        "key_corners": ["Turn 1", "Turn 7 (Sweepers)", "Turn 14"],
        "optimal_setup": "high_downforce",
        "team_historical_wins_since_2010": {
            "mercedes": 7,
            "ferrari": 4,
            "red_bull": 3,
            "mclaren": 2,
        },
        "driver_historical_wins": {
            "hamilton": 5,
            "vettel": 3,
            "raikkonen": 2,
            "rosberg": 2,
            "alonso": 1,
        },
        "notes": "Unique figure-8 layout with massive elevation change at Turn 1. DRS train risk.",
    },
    "monaco": {
        "id": "monaco",
        "name": "Circuit de Monaco",
        "city": "Monte Carlo",
        "country": "Monaco",
        "round_2026": 6,
        "race_date": "2026-06-07",
        "sprint_weekend": False,
        "circuit_type": ["technical", "street"],
        "lap_count": 78,
        "lap_distance_km": 3.337,
        "total_distance_km": 260.286,
        "safety_car_probability": 0.78,
        "overtaking_difficulty": 10,
        "power_unit_demand": 4.5,
        "brake_demand": 9.0,
        "tire_deg_rate": 3.0,
        "active_aero_demand": 9.5,
        "rain_probability_typical": 0.30,
        "wall_crash_probability_per_lap": 0.006,
        "drs_zones": 1,
        "overtake_zones": ["Main straight"],
        "key_corners": ["Turn 1", "Turn 3", "Turn 6 (Grand Hotel)"],
        "optimal_setup": "high_downforce",
        "team_historical_wins_since_2010": {
            "mercedes": 8,
            "ferrari": 4,
            "red_bull": 3,
            "mclaren": 2,
        },
        "driver_historical_wins": {
            "hamilton": 6,
            "vettel": 3,
            "rosberg": 2,
            "alonso": 1,
            "raikkonen": 1,
        },
        "notes": "Tight street circuit with no overtaking outside DRS zone. High accident risk.",
    },
}

CIRCUITS: dict = {
    "canada": {
        "id": "canada",
        "name": "Circuit Gilles-Villeneuve",
        "city": "Montreal",
        "country": "Canada",
        "round_2026": 5,
        "race_date": "2026-05-24",
        "sprint_weekend": True,
        "circuit_type": ["power_unit", "street"],
        "lap_count": 70,
        "lap_distance_km": 4.361,
        "total_distance_km": 305.27,
        "safety_car_probability": 0.82,        # Highest on calendar
        "overtaking_difficulty": 4,             # Relatively easy (long straight)
        "power_unit_demand": 8.5,
        "brake_demand": 8.5,
        "tire_deg_rate": 6.0,
        "active_aero_demand": 8.0,
        "rain_probability_typical": 0.35,       # Late May Montreal
        "wall_crash_probability_per_lap": 0.004, # Wall of Champions effect
        "drs_zones": 2,
        "overtake_zones": ["Pit straight", "After Hairpin"],
        "key_corners": ["Turn 1–2 chicane", "Turn 10 Hairpin", "Wall of Champions"],
        "optimal_setup": "low_drag",
        "team_historical_wins_since_2010": {
            "mercedes": 10,
            "red_bull": 8,
            "ferrari": 4,
            "mclaren": 2,
            "renault": 1,
            "williams": 0,
        },
        "driver_historical_wins": {
            "hamilton": 7,
            "verstappen": 5,
            "vettel": 3,
            "alonso": 2,
            "button": 2,
        },
        "notes": "Stop-start island circuit. Wall of Champions catches title-fight leaders regularly.",
    },
    "australia": {
        "id": "australia",
        "name": "Albert Park Circuit",
        "city": "Melbourne",
        "country": "Australia",
        "round_2026": 1,
        "race_date": "2026-03-08",
        "sprint_weekend": False,
        "circuit_type": ["street", "balanced"],
        "lap_count": 58,
        "lap_distance_km": 5.303,
        "total_distance_km": 307.574,
        "safety_car_probability": 0.68,
        "overtaking_difficulty": 6,
        "power_unit_demand": 6.5,
        "brake_demand": 7.0,
        "tire_deg_rate": 5.5,
        "active_aero_demand": 7.0,
        "rain_probability_typical": 0.25,
        "wall_crash_probability_per_lap": 0.003,
        "drs_zones": 3,
        "team_historical_wins_since_2010": {
            "mercedes": 7,
            "red_bull": 5,
            "ferrari": 3,
            "mclaren": 1,
        },
    },
    "china": {
        "id": "china",
        "name": "Shanghai International Circuit",
        "city": "Shanghai",
        "country": "China",
        "round_2026": 2,
        "race_date": "2026-03-15",
        "sprint_weekend": True,
        "circuit_type": ["balanced", "high_downforce"],
        "lap_count": 56,
        "lap_distance_km": 5.451,
        "total_distance_km": 305.066,
        "safety_car_probability": 0.55,
        "overtaking_difficulty": 5,
        "power_unit_demand": 7.0,
        "brake_demand": 6.5,
        "tire_deg_rate": 7.5,
        "active_aero_demand": 7.5,
        "rain_probability_typical": 0.20,
        "wall_crash_probability_per_lap": 0.002,
        "drs_zones": 2,
        "team_historical_wins_since_2010": {
            "mercedes": 6,
            "red_bull": 6,
            "ferrari": 2,
            "mclaren": 2,
        },
    },
    "monaco": {
        "id": "monaco",
        "name": "Circuit de Monaco",
        "city": "Monte Carlo",
        "country": "Monaco",
        "round_2026": 6,
        "race_date": "2026-06-07",
        "sprint_weekend": False,
        "circuit_type": ["technical", "street"],
        "lap_count": 78,
        "lap_distance_km": 3.337,
        "total_distance_km": 260.286,
        "safety_car_probability": 0.78,
        "overtaking_difficulty": 10,
        "power_unit_demand": 4.5,
        "brake_demand": 9.0,
        "tire_deg_rate": 3.0,
        "active_aero_demand": 9.5,
        "rain_probability_typical": 0.30,
        "wall_crash_probability_per_lap": 0.006,
        "drs_zones": 1,
        "team_historical_wins_since_2010": {
            "mercedes": 8,
            "red_bull": 5,
            "ferrari": 3,
            "mclaren": 1,
        },
    },
}


# Process raw data with validation
CIRCUITS: Dict[str, CircuitData] = {}

def _validate_and_load_circuits():
    """Load and validate circuit data according to schema."""
    errors = []
    for circuit_id, raw_data in CIRCUIT_DATA_RAW.items():
        try:
            validated_circuit = CircuitData(**raw_data)
            CIRCUITS[validated_circuit.id] = validated_circuit
        except Exception as e:
            errors.append(f"Circuit {circuit_id}: {str(e)}")
    
    if errors:
        error_msg = "Validation errors in circuit data:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

_validate_and_load_circuits()


# ── Access Functions ───────────────────────────────────────────────────────────

def get_circuit(circuit_id: str) -> CircuitData:
    """Get circuit data by ID.

    Note: tests and some engine code expect dict-like access (e.g. c["safety_car_probability"]).
    CircuitData is a pydantic model, so we return its dict for compatibility.
    """
    if circuit_id not in CIRCUITS:
        raise KeyError(f"No circuit found with ID: {circuit_id}")
    return CIRCUITS[circuit_id].model_dump()


def get_all_circuits() -> List[CircuitData]:
    """Return list of all validated circuits."""
    return list(CIRCUITS.values())


def circuit_favors_team(circuit_id: str, team_id: str) -> float:
    """Get a multiplier representing how much the circuit favors a specific team."""
    circuit = get_circuit(circuit_id)
    wins_by_team = circuit.team_historical_wins_since_2010 or {}
    
    # Base multiplier of 1.0 (no advantage either way)
    max_wins = max(wins_by_team.values()) if wins_by_team else 0
    if max_wins == 0:
        return 1.0
    
    team_wins = wins_by_team.get(team_id, 0)
    # Scale between 0.9 and 1.1 based on win history
    return 0.9 + (0.2 * team_wins / max_wins)


def validate_circuit_data_integrity():
    """Run integrity checks on circuit data."""
    errors = []
    
    for circuit_id, circuit in CIRCUITS.items():
        # Check that required fields exist
        if not circuit.name or not circuit.country:
            errors.append(f"Circuit {circuit_id} missing required fields")
        
        # Check probability ranges
        if not (0.0 <= circuit.safety_car_probability <= 1.0):
            errors.append(f"Circuit {circuit_id} has invalid safety_car_probability: {circuit.safety_car_probability}")
        
        if not (0.0 <= circuit.rain_probability_typical <= 1.0):
            errors.append(f"Circuit {circuit_id} has invalid rain_probability_typical: {circuit.rain_probability_typical}")
        
        # Check difficulty ranges
        if not (1 <= circuit.overtaking_difficulty <= 10):
            errors.append(f"Circuit {circuit_id} has invalid overtaking_difficulty: {circuit.overtaking_difficulty}")
        
        if not (0.0 <= circuit.power_unit_demand <= 10.0):
            errors.append(f"Circuit {circuit_id} has invalid power_unit_demand: {circuit.power_unit_demand}")
        
        if not (0.0 <= circuit.brake_demand <= 10.0):
            errors.append(f"Circuit {circuit_id} has invalid brake_demand: {circuit.brake_demand}")
    
    if errors:
        error_msg = "Data integrity issues found:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
