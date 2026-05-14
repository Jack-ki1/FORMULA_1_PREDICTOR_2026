"""
F1 Circuit Database — 2026 Season

Each circuit entry contains:
  - circuit_type: primary classification
  - safety_car_probability: historical SC occurrence rate
  - overtaking_difficulty: 1-10 (10 = near impossible)
  - power_unit_demand: 1-10
  - brake_demand: 1-10
  - tire_deg_rate: 1-10
  - rain_probability_typical: climatological rain chance for race date
  - wall_crash_probability: probability of pit-lane/barrier incident per lap
  - lap_count: race laps
  - lap_distance_km: lap length
  - drs_zones: number of DRS/overtake zones
  - team_historical_wins: map of team → win count since 2010
"""

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


def get_circuit(circuit_id: str) -> dict:
    """Return circuit data by ID."""
    c = CIRCUITS.get(circuit_id)
    if not c:
        raise KeyError(f"Circuit '{circuit_id}' not found.")
    return c


def get_all_circuits() -> list:
    """Return all circuit records."""
    return list(CIRCUITS.values())


def circuit_favors_team(circuit_id: str, team_id: str) -> float:
    """
    Return a multiplier [0.85–1.25] reflecting how much this circuit
    historically favours a team relative to field average.
    """
    circuit = get_circuit(circuit_id)
    wins = circuit.get("team_historical_wins_since_2010", {})
    total = sum(wins.values()) or 1
    team_wins = wins.get(team_id, 0)
    share = team_wins / total
    # Normalise so 0.25 share → 1.25, 0 share → 0.85
    return 0.85 + (share * 1.60)
