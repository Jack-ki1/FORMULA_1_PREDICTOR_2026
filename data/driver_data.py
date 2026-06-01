"""
Driver Data — 22 Driver Profiles for F1 Prediction System v3.0.

Contains all driver information including:
  - Basic profile data (name, team, nationality)
  - Performance metrics (ELO, skills, DNF rates)
  - Season statistics (points, wins)
  - Track type preferences
  - Recent form data

Expected structure for all functions and constants.
"""

from typing import Dict, List, Any, Optional


# Main driver data dictionary - based on typical 2026 driver lineup
DRIVERS: Dict[str, Dict[str, Any]] = {
    # Mercedes
    "antonelli": {
        "id": "antonelli",
        "name": "Kimi Antonelli",
        "short": "ANT",
        "team": "mercedes",
        "nationality": "Italian",
        "number": 15,
        "experience_races": 15,
        "elo": 1650,
        "wet_skill": 8.5,
        "brakezone_skill": 8.2,
        "tire_management": 8.8,
        "qualifying_delta_avg": 0.15,
        "dnf_rate_career": 0.08,
        "dnf_rate_recent": 0.05,
        "track_type_fit": {
            "high_downforce": 0.98,
            "technical": 0.95,
            "power_unit": 0.92,
            "street": 0.88,
            "balanced": 0.96
        },
        "recent_form": [1, 2, 1, 3, 1, 2],  # Last 6 results
        "championship_points_2026": 105,
        "wins_2026": 3,
        "active": True
    },
    "russell": {
        "id": "russell",
        "name": "George Russell",
        "short": "RUS",
        "team": "mercedes",
        "nationality": "British",
        "number": 63,
        "experience_races": 103,
        "elo": 1620,
        "wet_skill": 8.0,
        "brakezone_skill": 8.5,
        "tire_management": 8.5,
        "qualifying_delta_avg": 0.18,
        "dnf_rate_career": 0.12,
        "dnf_rate_recent": 0.08,
        "track_type_fit": {
            "high_downforce": 0.95,
            "technical": 0.93,
            "power_unit": 0.96,
            "street": 0.92,
            "balanced": 0.94
        },
        "recent_form": [3, 2, 4, 2, 3, 2],
        "championship_points_2026": 75,
        "wins_2026": 0,
        "active": True
    },
    "hamilton": {
        "id": "hamilton",
        "name": "Lewis Hamilton",
        "short": "HAM",
        "team": "ferrari",
        "nationality": "British",
        "number": 44,
        "experience_races": 334,
        "elo": 1630,
        "wet_skill": 9.0,
        "brakezone_skill": 8.8,
        "tire_management": 9.0,
        "qualifying_delta_avg": 0.10,
        "dnf_rate_career": 0.10,
        "dnf_rate_recent": 0.08,
        "track_type_fit": {
            "high_downforce": 0.98,
            "technical": 0.95,
            "power_unit": 0.92,
            "street": 0.95,
            "balanced": 0.97
        },
        "recent_form": [7, 9, 8, 9, 7, 8],
        "championship_points_2026": 32,
        "wins_2026": 0,
        "active": True
    },
    
    # McLaren
    "norris": {
        "id": "norris",
        "name": "Lando Norris",
        "short": "NOR",
        "team": "mclaren",
        "nationality": "British",
        "number": 4,
        "experience_races": 103,
        "elo": 1600,
        "wet_skill": 8.8,
        "brakezone_skill": 8.0,
        "tire_management": 8.2,
        "qualifying_delta_avg": 0.12,
        "dnf_rate_career": 0.10,
        "dnf_rate_recent": 0.09,
        "track_type_fit": {
            "high_downforce": 0.92,
            "technical": 0.96,
            "power_unit": 0.88,
            "street": 0.95,
            "balanced": 0.94
        },
        "recent_form": [4, 3, 2, 4, 2, 3],
        "championship_points_2026": 68,
        "wins_2026": 1,
        "active": True
    },
    "piastri": {
        "id": "piastri",
        "name": "Oscar Piastri",
        "short": "PIA",
        "team": "mclaren",
        "nationality": "Australian",
        "number": 81,
        "experience_races": 52,
        "elo": 1580,
        "wet_skill": 8.2,
        "brakezone_skill": 8.6,
        "tire_management": 8.6,
        "qualifying_delta_avg": 0.10,
        "dnf_rate_career": 0.15,
        "dnf_rate_recent": 0.12,
        "track_type_fit": {
            "high_downforce": 0.90,
            "technical": 0.94,
            "power_unit": 0.85,
            "street": 0.93,
            "balanced": 0.92
        },
        "recent_form": [5, 5, 3, 5, 4, 4],
        "championship_points_2026": 52,
        "wins_2026": 0,
        "active": True
    },
    
    # Red Bull
    "verstappen": {
        "id": "verstappen",
        "name": "Max Verstappen",
        "short": "VER",
        "team": "red_bull",
        "nationality": "Dutch",
        "number": 1,
        "experience_races": 166,
        "elo": 1680,
        "wet_skill": 9.2,
        "brakezone_skill": 9.0,
        "tire_management": 8.8,
        "qualifying_delta_avg": 0.08,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.15,
        "track_type_fit": {
            "high_downforce": 0.98,
            "technical": 0.97,
            "power_unit": 0.95,
            "street": 0.96,
            "balanced": 0.97
        },
        "recent_form": [2, 1, 1, 1, 1, 1],
        "championship_points_2026": 93,
        "wins_2026": 2,
        "active": True
    },
    "hadjar": {
        "id": "hadjar",
        "name": "Isack Hadjar",
        "short": "HAD",
        "team": "red_bull",
        "nationality": "French",
        "number": 6,
        "experience_races": 1,
        "elo": 1450,
        "wet_skill": 7.2,
        "brakezone_skill": 7.5,
        "tire_management": 7.3,
        "qualifying_delta_avg": 0.35,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.15,
        "track_type_fit": {
            "high_downforce": 0.85,
            "technical": 0.82,
            "power_unit": 0.80,
            "street": 0.83,
            "balanced": 0.84
        },
        "recent_form": [0, 0, 0, 0, 0, 5],
        "championship_points_2026": 4,
        "wins_2026": 0,
        "active": True
    },
    "perez": {
        "id": "perez",
        "name": "Sergio Perez",
        "short": "PER",
        "team": "cadillac",
        "nationality": "Mexican",
        "number": 11,
        "experience_races": 234,
        "elo": 1550,
        "wet_skill": 7.8,
        "brakezone_skill": 8.2,
        "tire_management": 8.8,
        "qualifying_delta_avg": 0.25,
        "dnf_rate_career": 0.22,
        "dnf_rate_recent": 0.18,
        "track_type_fit": {
            "high_downforce": 0.90,
            "technical": 0.88,
            "power_unit": 0.85,
            "street": 0.87,
            "balanced": 0.89
        },
        "recent_form": [6, 7, 5, 3, 5, 4],
        "championship_points_2026": 45,
        "wins_2026": 1,
        "active": True
    },
    
    # Ferrari
    "leclerc": {
        "id": "leclerc",
        "name": "Charles Leclerc",
        "short": "LEC",
        "team": "ferrari",
        "nationality": "Monegasque",
        "number": 16,
        "experience_races": 125,
        "elo": 1590,
        "wet_skill": 8.5,
        "brakezone_skill": 8.8,
        "tire_management": 8.0,
        "qualifying_delta_avg": 0.09,
        "dnf_rate_career": 0.25,
        "dnf_rate_recent": 0.20,
        "track_type_fit": {
            "high_downforce": 0.96,
            "technical": 0.95,
            "power_unit": 0.88,
            "street": 0.92,
            "balanced": 0.94
        },
        "recent_form": [7, 4, 6, 6, 3, 2],
        "championship_points_2026": 57,
        "wins_2026": 0,
        "active": True
    },
    "sainz": {
        "id": "sainz",
        "name": "Carlos Sainz",
        "short": "SAI",
        "team": "williams",
        "nationality": "Spanish",
        "number": 55,
        "experience_races": 180,
        "elo": 1570,
        "wet_skill": 8.0,
        "brakezone_skill": 8.4,
        "tire_management": 8.6,
        "qualifying_delta_avg": 0.18,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.14,
        "track_type_fit": {
            "high_downforce": 0.92,
            "technical": 0.90,
            "power_unit": 0.85,
            "street": 0.90,
            "balanced": 0.91
        },
        "recent_form": [8, 6, 4, 7, 6, 5],
        "championship_points_2026": 48,
        "wins_2026": 0,
        "active": True
    },
    
    # Williams
    "albon": {
        "id": "albon",
        "name": "Alex Albon",
        "short": "ALB",
        "team": "williams",
        "nationality": "Thai-British",
        "number": 23,
        "experience_races": 76,
        "elo": 1520,
        "wet_skill": 8.0,
        "brakezone_skill": 7.8,
        "tire_management": 8.4,
        "qualifying_delta_avg": 0.22,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.16,
        "track_type_fit": {
            "high_downforce": 0.88,
            "technical": 0.85,
            "power_unit": 0.82,
            "street": 0.86,
            "balanced": 0.87
        },
        "recent_form": [10, 9, 8, 9, 8, 7],
        "championship_points_2026": 3,
        "wins_2026": 0,
        "active": True
    },
    "bottas": {
        "id": "bottas",
        "name": "Valtteri Bottas",
        "short": "BOT",
        "team": "cadillac",
        "nationality": "Finnish",
        "number": 77,
        "experience_races": 200,
        "elo": 1530,
        "wet_skill": 7.8,
        "brakezone_skill": 8.0,
        "tire_management": 8.5,
        "qualifying_delta_avg": 0.20,
        "dnf_rate_career": 0.15,
        "dnf_rate_recent": 0.12,
        "track_type_fit": {
            "high_downforce": 0.90,
            "technical": 0.88,
            "power_unit": 0.85,
            "street": 0.87,
            "balanced": 0.89
        },
        "recent_form": [9, 8, 7, 8, 7, 6],
        "championship_points_2026": 1,
        "wins_2026": 0,
        "active": True
    },
    
    # Alpine
    "gasly": {
        "id": "gasly",
        "name": "Pierre Gasly",
        "short": "GAS",
        "team": "alpine",
        "nationality": "French",
        "number": 10,
        "experience_races": 142,
        "elo": 1510,
        "wet_skill": 8.0,
        "brakezone_skill": 8.2,
        "tire_management": 8.4,
        "qualifying_delta_avg": 0.20,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.14,
        "track_type_fit": {
            "high_downforce": 0.90,
            "technical": 0.88,
            "power_unit": 0.85,
            "street": 0.88,
            "balanced": 0.89
        },
        "recent_form": [7, 8, 5, 6, 7, 6],
        "championship_points_2026": 4,
        "wins_2026": 0,
        "active": True
    },
    "colapinto": {
        "id": "colapinto",
        "name": "Franco Colapinto",
        "short": "COL",
        "team": "alpine",
        "nationality": "Argentine",
        "number": 43,
        "experience_races": 5,
        "elo": 1430,
        "wet_skill": 7.0,
        "brakezone_skill": 7.3,
        "tire_management": 7.2,
        "qualifying_delta_avg": 0.38,
        "dnf_rate_career": 0.20,
        "dnf_rate_recent": 0.18,
        "track_type_fit": {
            "high_downforce": 0.82,
            "technical": 0.80,
            "power_unit": 0.78,
            "street": 0.81,
            "balanced": 0.81
        },
        "recent_form": [0, 0, 0, 0, 0, 6],
        "championship_points_2026": 3,
        "wins_2026": 0,
        "active": True
    },
    
    # Haas
    "ocon": {
        "id": "ocon",
        "name": "Esteban Ocon",
        "short": "OCO",
        "team": "haas",
        "nationality": "French",
        "number": 31,
        "experience_races": 136,
        "elo": 1500,
        "wet_skill": 7.8,
        "brakezone_skill": 8.0,
        "tire_management": 8.2,
        "qualifying_delta_avg": 0.20,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.15,
        "track_type_fit": {
            "high_downforce": 0.90,
            "technical": 0.88,
            "power_unit": 0.85,
            "street": 0.87,
            "balanced": 0.89
        },
        "recent_form": [10, 11, 10, 11, 9, 10],
        "championship_points_2026": 18,
        "wins_2026": 0,
        "active": True
    },
    "bearman": {
        "id": "bearman",
        "name": "Oliver Bearman",
        "short": "BEA",
        "team": "haas",
        "nationality": "British",
        "number": 87,
        "experience_races": 3,
        "elo": 1440,
        "wet_skill": 7.1,
        "brakezone_skill": 7.4,
        "tire_management": 7.3,
        "qualifying_delta_avg": 0.36,
        "dnf_rate_career": 0.19,
        "dnf_rate_recent": 0.17,
        "track_type_fit": {
            "high_downforce": 0.83,
            "technical": 0.81,
            "power_unit": 0.79,
            "street": 0.82,
            "balanced": 0.82
        },
        "recent_form": [0, 0, 0, 0, 0, 10],
        "championship_points_2026": 1,
        "wins_2026": 0,
        "active": True
    },
    
    # Aston Martin
    "alonso": {
        "id": "alonso",
        "name": "Fernando Alonso",
        "short": "ALO",
        "team": "aston_martin",
        "nationality": "Spanish",
        "number": 14,
        "experience_races": 397,
        "elo": 1560,
        "wet_skill": 8.2,
        "brakezone_skill": 8.6,
        "tire_management": 8.5,
        "qualifying_delta_avg": 0.15,
        "dnf_rate_career": 0.15,
        "dnf_rate_recent": 0.12,
        "track_type_fit": {
            "high_downforce": 0.95,
            "technical": 0.93,
            "power_unit": 0.90,
            "street": 0.92,
            "balanced": 0.94
        },
        "recent_form": [9, 8, 9, 10, 8, 9],
        "championship_points_2026": 26,
        "wins_2026": 0,
        "active": True
    },
    "stroll": {
        "id": "stroll",
        "name": "Lance Stroll",
        "short": "STR",
        "team": "aston_martin",
        "nationality": "Canadian",
        "number": 18,
        "experience_races": 136,
        "elo": 1470,
        "wet_skill": 7.2,
        "brakezone_skill": 7.8,
        "tire_management": 8.0,
        "qualifying_delta_avg": 0.25,
        "dnf_rate_career": 0.18,
        "dnf_rate_recent": 0.15,
        "track_type_fit": {
            "high_downforce": 0.88,
            "technical": 0.85,
            "power_unit": 0.82,
            "street": 0.85,
            "balanced": 0.86
        },
        "recent_form": [13, 12, 11, 12, 11, 10],
        "championship_points_2026": 11,
        "wins_2026": 0,
        "active": True
    },
    
    # Audi
    "hulkenberg": {
        "id": "hulkenberg",
        "name": "Nico Hulkenberg",
        "short": "HUL",
        "team": "audi",
        "nationality": "German",
        "number": 27,
        "experience_races": 155,
        "elo": 1480,
        "wet_skill": 7.5,
        "brakezone_skill": 7.8,
        "tire_management": 8.0,
        "qualifying_delta_avg": 0.25,
        "dnf_rate_career": 0.16,
        "dnf_rate_recent": 0.13,
        "track_type_fit": {
            "high_downforce": 0.85,
            "technical": 0.82,
            "power_unit": 0.80,
            "street": 0.83,
            "balanced": 0.84
        },
        "recent_form": [12, 11, 10, 11, 10, 9],
        "championship_points_2026": 12,
        "wins_2026": 0,
        "active": True
    },
    "bortoleto": {
        "id": "bortoleto",
        "name": "Gabriel Bortoleto",
        "short": "BOR",
        "team": "audi",
        "nationality": "Brazilian",
        "number": 5,
        "experience_races": 2,
        "elo": 1410,
        "wet_skill": 6.9,
        "brakezone_skill": 7.1,
        "tire_management": 7.0,
        "qualifying_delta_avg": 0.40,
        "dnf_rate_career": 0.22,
        "dnf_rate_recent": 0.20,
        "track_type_fit": {
            "high_downforce": 0.80,
            "technical": 0.78,
            "power_unit": 0.76,
            "street": 0.79,
            "balanced": 0.79
        },
        "recent_form": [0, 0, 0, 0, 0, 13],
        "championship_points_2026": 0,
        "wins_2026": 0,
        "active": True
    },
    
    # Racing Bulls
    "lawson": {
        "id": "lawson",
        "name": "Liam Lawson",
        "short": "LAW",
        "team": "rb",
        "nationality": "New Zealander",
        "number": 3,
        "experience_races": 2,
        "elo": 1420,
        "wet_skill": 7.0,
        "brakezone_skill": 7.2,
        "tire_management": 7.0,
        "qualifying_delta_avg": 0.40,
        "dnf_rate_career": 0.25,
        "dnf_rate_recent": 0.22,
        "track_type_fit": {
            "high_downforce": 0.78,
            "technical": 0.75,
            "power_unit": 0.72,
            "street": 0.76,
            "balanced": 0.76
        },
        "recent_form": [19, 18, 17, 18, 17, 16],
        "championship_points_2026": 0,
        "wins_2026": 0,
        "active": True
    },
    "lindblad": {
        "id": "lindblad",
        "name": "Arvid Lindblad",
        "short": "LIN",
        "team": "rb",
        "nationality": "Swedish",
        "number": 41,
        "experience_races": 1,
        "elo": 1400,
        "wet_skill": 6.8,
        "brakezone_skill": 7.0,
        "tire_management": 6.9,
        "qualifying_delta_avg": 0.42,
        "dnf_rate_career": 0.25,
        "dnf_rate_recent": 0.22,
        "track_type_fit": {
            "high_downforce": 0.78,
            "technical": 0.76,
            "power_unit": 0.74,
            "street": 0.77,
            "balanced": 0.77
        },
        "recent_form": [0, 0, 0, 0, 0, 22],
        "championship_points_2026": 0,
        "wins_2026": 0,
        "active": True
    }
}

def get_driver(driver_id: str) -> Dict[str, Any]:
    """Get a specific driver by ID."""
    if driver_id not in DRIVERS:
        raise KeyError(f"Driver '{driver_id}' not found")
    return DRIVERS[driver_id]


def get_all_drivers() -> List[Dict[str, Any]]:
    """Get all driver profiles."""
    return [driver for driver in DRIVERS.values() if driver.get("active", True)]


def get_drivers_for_team(team_id: str) -> List[Dict[str, Any]]:
    """Get all drivers for a specific team."""
    return [driver for driver in get_all_drivers() if driver["team"] == team_id]


def calculate_circuit_performance_modifier(driver_id: str, circuit_id: str) -> float:
    """
    Calculate circuit-specific performance modifier for a driver.
    Based on historical performance at the circuit.
    """
    # This is a simplified version - in reality would use DRIVER_TRAITS_DB
    base_modifier = 1.0
    
    # Different circuits favor different driving styles
    circuit_favorable_types = {
        "monaco": ["technical", "street"],
        "silverstone": ["high_downforce", "balanced"],
        "spa": ["power_unit", "balanced"],
        "monza": ["power_unit"],
        "baku": ["high_downforce", "street"]
    }
    
    if circuit_id in circuit_favorable_types:
        favorable_types = circuit_favorable_types[circuit_id]
        driver = get_driver(driver_id)
        track_fit = driver.get("track_type_fit", {})
        
        # Find the best matching type
        max_fit = 0.9  # Default neutral
        for fit_type in favorable_types:
            if fit_type in track_fit:
                max_fit = max(max_fit, track_fit[fit_type])
        
        # Apply small adjustment based on fit
        base_modifier = max_fit
    
    return base_modifier


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "DRIVERS", 
    "get_driver", 
    "get_all_drivers", 
    "get_drivers_for_team", 
    "calculate_circuit_performance_modifier"
]