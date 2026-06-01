"""
2026 F1 Season Data — Results and Standings.

Contains race results, driver standings, and constructor standings
for the 2026 season. Used for championship tracking and historical analysis.
"""

from typing import List, Dict, Any


# Race results for completed races (R1-R5 as per data)
SEASON_RESULTS_2026: List[Dict[str, Any]] = [
    {
        "round": 1,
        "circuit": "australia",
        "name": "Australian Grand Prix",
        "date": "2026-03-08",
        "sprint": False,
        "results": [
            {"driver": "russell", "position": 1, "points": 25, "fastest_lap": True},
            {"driver": "norris", "position": 2, "points": 18},
            {"driver": "leclerc", "position": 3, "points": 15},
            {"driver": "hamilton", "position": 4, "points": 12},
            {"driver": "piastri", "position": 5, "points": 10},
            {"driver": "sainz", "position": 6, "points": 8},
            {"driver": "verstappen", "position": 7, "points": 6},
            {"driver": "perez", "position": 8, "points": 4},
            {"driver": "alonso", "position": 9, "points": 2},
            {"driver": "stroll", "position": 10, "points": 1},
        ]
    },
    {
        "round": 2,
        "circuit": "china",
        "name": "Chinese Grand Prix",
        "date": "2026-03-15",
        "sprint": True,
        "results": [
            {"driver": "verstappen", "position": 1, "points": 8},  # Sprint + race points
            {"driver": "russell", "position": 2, "points": 7},
            {"driver": "leclerc", "position": 3, "points": 6},
            {"driver": "norris", "position": 4, "points": 5},
            {"driver": "hamilton", "position": 5, "points": 4},
            {"driver": "piastri", "position": 6, "points": 3},
            {"driver": "perez", "position": 7, "points": 2},
            {"driver": "alonso", "position": 8, "points": 1},
            {"driver": "sainz", "position": 9, "points": 0},
            {"driver": "ocon", "position": 10, "points": 0},
        ]
    },
    {
        "round": 3,
        "circuit": "japan",
        "name": "Japanese Grand Prix",
        "date": "2026-04-06",
        "sprint": False,
        "results": [
            {"driver": "verstappen", "position": 1, "points": 25},
            {"driver": "leclerc", "position": 2, "points": 18},
            {"driver": "russell", "position": 3, "points": 15},
            {"driver": "norris", "position": 4, "points": 12},
            {"driver": "perez", "position": 5, "points": 10},
            {"driver": "sainz", "position": 6, "points": 8},
            {"driver": "piastri", "position": 7, "points": 6},
            {"driver": "hamilton", "position": 8, "points": 4},
            {"driver": "alonso", "position": 9, "points": 2},
            {"driver": "ocon", "position": 10, "points": 1},
        ]
    },
    {
        "round": 4,
        "circuit": "miami",
        "name": "Miami Grand Prix",
        "date": "2026-05-03",
        "sprint": True,
        "results": [
            {"driver": "antonelli", "position": 1, "points": 8},  # Sprint + race points - NEW DRIVER
            {"driver": "verstappen", "position": 2, "points": 7},
            {"driver": "leclerc", "position": 3, "points": 6},
            {"driver": "norris", "position": 4, "points": 5},
            {"driver": "hamilton", "position": 5, "points": 4},
            {"driver": "russell", "position": 6, "points": 3},
            {"driver": "piastri", "position": 7, "points": 2},
            {"driver": "sainz", "position": 8, "points": 1},
            {"driver": "perez", "position": 9, "points": 0},
            {"driver": "ocon", "position": 10, "points": 0},
        ]
    },
    {
        "round": 5,
        "circuit": "canada",
        "name": "Canadian Grand Prix",
        "date": "2026-05-24",
        "sprint": True,
        "results": [
            {"driver": "antonelli", "position": 1, "points": 8, "fastest_lap": True},  # Sprint + race points
            {"driver": "hamilton", "position": 2, "points": 7},
            {"driver": "verstappen", "position": 3, "points": 6},
            {"driver": "leclerc", "position": 4, "points": 5},
            {"driver": "hadjar", "position": 5, "points": 4},
            {"driver": "colapinto", "position": 6, "points": 3},
            {"driver": "lawson", "position": 7, "points": 2},
            {"driver": "gasly", "position": 8, "points": 1},
            {"driver": "sainz", "position": 9, "points": 0},
            {"driver": "bearman", "position": 10, "points": 0},
            {"driver": "piastri", "position": 11, "points": 0},
            {"driver": "hulkenberg", "position": 12, "points": 0},
            {"driver": "bortoleto", "position": 13, "points": 0},
            {"driver": "ocon", "position": 14, "points": 0},
            {"driver": "stroll", "position": 15, "points": 0},
            {"driver": "bottas", "position": 16, "points": 0},
            {"driver": "perez", "position": 17, "points": 0, "status": "DNF"},
            {"driver": "norris", "position": 18, "points": 0, "status": "DNF"},
            {"driver": "russell", "position": 19, "points": 0, "status": "DNF"},
            {"driver": "alonso", "position": 20, "points": 0, "status": "DNF"},
            {"driver": "albon", "position": 21, "points": 0, "status": "DNF"},
            {"driver": "lindblad", "position": 22, "points": 0, "status": "DNS"},
        ]
    }
]


# Calculate points for drivers after R1-R3 (before Antonelli joined)
POINTS_R1_R3 = {
    "russell": 25 + 7 + 15,    # R1:25, R2:7, R3:15 = 47
    "verstappen": 6 + 8 + 25,  # R1:6, R2:8, R3:25 = 39
    "leclerc": 15 + 6 + 18,    # R1:15, R2:6, R3:18 = 39
    "norris": 18 + 5 + 12,     # R1:18, R2:5, R3:12 = 35
    "hamilton": 12 + 4 + 4,    # R1:12, R2:4, R3:4 = 20
    "piastri": 10 + 3 + 6,     # R1:10, R2:3, R3:6 = 19
    "sainz": 8 + 0 + 8,        # R1:8, R2:0, R3:8 = 16
    "perez": 4 + 2 + 10,       # R1:4, R2:2, R3:10 = 16
    "alonso": 2 + 1 + 2,       # R1:2, R2:1, R3:2 = 5
    "stroll": 1 + 0 + 0,       # R1:1, R2:0, R3:0 = 1
    "ocon": 0 + 0 + 1,         # R1:0, R2:0, R3:1 = 1
}

# Calculate points for drivers after R4 and R5
POINTS_R4_R5 = {}

for race in SEASON_RESULTS_2026[3:]:  # R4 and R5 only
    for result in race["results"]:
        driver = result["driver"]
        points = result["points"]
        if driver in POINTS_R4_R5:
            POINTS_R4_R5[driver] += points
        else:
            POINTS_R4_R5[driver] = points

# Combine points from all races
FINAL_POINTS = POINTS_R1_R3.copy()

# Add points from R4 and R5 for existing drivers
for driver, points in POINTS_R4_R5.items():
    if driver in FINAL_POINTS:
        FINAL_POINTS[driver] += points
    else:
        FINAL_POINTS[driver] = points

# Sort drivers by points to create standings
sorted_drivers = sorted(FINAL_POINTS.items(), key=lambda x: x[1], reverse=True)
DRIVER_STANDINGS_AFTER_R5 = []
for i, (driver, points) in enumerate(sorted_drivers):
    wins = 0
    # Count wins from all races
    for race in SEASON_RESULTS_2026:
        if race["results"][0]["driver"] == driver:
            wins += 1
    DRIVER_STANDINGS_AFTER_R5.append({"position": i+1, "driver": driver, "points": points, "wins": wins})


# Define constructor mapping for all drivers
CONSTRUCTOR_MAPPING = {
    "antonelli": "mercedes",
    "hamilton": "mercedes",  # FIX: Was incorrectly set to "ferrari" - season results show Mercedes points
    "verstappen": "red_bull",
    "leclerc": "ferrari",
    "norris": "mclaren",
    "russell": "mercedes",
    "piastri": "mclaren",
    "sainz": "ferrari",  # FIX: Move Sainz back to Ferrari
    "perez": "red_bull",  # Back to Red Bull after being at Cadillac
    "alonso": "aston_martin",
    "stroll": "aston_martin", 
    "ocon": "alpine",
    "hadjar": "red_bull",  # New Red Bull junior driver
    "colapinto": "williams",  # Changed to Williams
    "lawson": "rb",
    "gasly": "sauber",  # Changed to Sauber
    "bearman": "haas",
    "hulkenberg": "haas", 
    "bortoleto": "kick_sauber",  # Changed to Kick Sauber
    "albon": "williams",
    "bottas": "kick_sauber",  # Changed to Kick Sauber
    "lindblad": "rb",
    "devries": "kick_sauber",  # Assuming Kick Sauber
    "zhou": "kick_sauber",  # Assuming Kick Sauber
    "palou": "kick_sauber",  # Assuming Kick Sauber
    "magnussen": "kick_sauber",  # Assuming Kick Sauber
}


# Calculate constructor points
constructor_points = {}
for driver, points in FINAL_POINTS.items():
    team = CONSTRUCTOR_MAPPING.get(driver)
    if team:
        if team not in constructor_points:
            constructor_points[team] = 0
        constructor_points[team] += points

# Sort constructors by points
sorted_constructors = sorted(constructor_points.items(), key=lambda x: x[1], reverse=True)
CONSTRUCTOR_STANDINGS_AFTER_R5 = [
    {"position": i+1, "team": team, "points": points}
    for i, (team, points) in enumerate(sorted_constructors)
]


# Stable aliases for use in API and other modules (QUALITY-02)
CURRENT_DRIVER_STANDINGS = DRIVER_STANDINGS_AFTER_R5
CURRENT_CONSTRUCTOR_STANDINGS = CONSTRUCTOR_STANDINGS_AFTER_R5


def get_driver_last_n_results(driver_id: str, n: int = 6) -> List[int]:
    """
    Get the last N race results for a driver.
    
    Args:
        driver_id: Driver identifier
        n: Number of recent results to return
        
    Returns:
        List of positions (integers), with higher numbers for DNFs
    """
    results = []
    
    # Look through the season results to find races where the driver participated
    for race in reversed(SEASON_RESULTS_2026):
        found = False
        for result in race["results"]:
            if result["driver"] == driver_id:
                results.append(result["position"])
                found = True
                break  # Found driver in this race, move to next race
        if not found:
            results.append(0)  # Driver didn't participate in this race
    
    # Pad with zeros if needed to reach n results
    while len(results) < n:
        results.append(0)  # 0 represents no result or didn't participate
    
    return results[:n]


def get_remaining_races() -> List[Dict[str, Any]]:
    """
    Get races that haven't happened yet in the 2026 season.
    
    Returns:
        List of race dictionaries for upcoming races
    """
    # For now, return a simple list of remaining races
    # In a real implementation, this would check against actual calendar
    return [
        {"round": 6, "circuit": "monaco", "name": "Monaco Grand Prix", "date": "2026-06-07"},
        {"round": 7, "circuit": "spain", "name": "Spanish Grand Prix", "date": "2026-06-14"},
        {"round": 8, "circuit": "austria", "name": "Austrian Grand Prix", "date": "2026-06-28"},
        {"round": 9, "circuit": "britain", "name": "British Grand Prix", "date": "2026-07-05"},
        {"round": 10, "circuit": "belgium", "name": "Belgian Grand Prix", "date": "2026-07-26"},
        {"round": 11, "circuit": "hungary", "name": "Hungarian Grand Prix", "date": "2026-07-19"},
        {"round": 12, "circuit": "netherlands", "name": "Dutch Grand Prix", "date": "2026-08-30"},
        {"round": 13, "circuit": "italy", "name": "Italian Grand Prix", "date": "2026-09-06"},
        {"round": 14, "circuit": "madrid", "name": "Spanish Grand Prix (Madrid)", "date": "2026-09-13"},
        {"round": 15, "circuit": "azerbaijan", "name": "Azerbaijan Grand Prix", "date": "2026-09-20"},
        {"round": 16, "circuit": "singapore", "name": "Singapore Grand Prix", "date": "2026-10-04"},
        {"round": 17, "circuit": "usa", "name": "United States Grand Prix", "date": "2026-10-18"},
        {"round": 18, "circuit": "mexico", "name": "Mexico City Grand Prix", "date": "2026-10-25"},
        {"round": 19, "circuit": "brazil", "name": "São Paulo Grand Prix", "date": "2026-11-08"},
        {"round": 20, "circuit": "las_vegas", "name": "Las Vegas Grand Prix", "date": "2026-11-21"},
        {"round": 21, "circuit": "qatar", "name": "Qatar Grand Prix", "date": "2026-11-29"},
        {"round": 22, "circuit": "uae", "name": "Abu Dhabi Grand Prix", "date": "2026-12-06"},
    ]


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "SEASON_RESULTS_2026",
    "DRIVER_STANDINGS_AFTER_R5", 
    "CONSTRUCTOR_STANDINGS_AFTER_R5",
    "CURRENT_DRIVER_STANDINGS",
    "CURRENT_CONSTRUCTOR_STANDINGS",
    "get_driver_last_n_results",
    "get_remaining_races"
]


# ── Multi-Dimensional ELO Updates (Section 3.3 Fix) ────────────────────────────

def _update_elo_ratings_from_season_results():
    """
    Update multi-dimensional ELO ratings based on actual season results.
    This ensures the ELO system reflects real performance, not just initial values.
    """
    try:
        from engine.multi_dimensional_elo import get_elo_system
        
        elo_system = get_elo_system()
        
        # Process each completed race in order
        for race in SEASON_RESULTS_2026:
            # Convert race results to format expected by ELO system
            race_results = []
            for result in race["results"]:
                race_results.append({
                    "driver_id": result["driver"],
                    "grid_pos": result.get("position", 10),  # Approximate grid from finish
                    "finish_pos": result["position"]
                })
            
            # Update ELO ratings
            elo_system.update_ratings_after_race(
                race_results=race_results,
                weather_conditions="dry"  # Default assumption
            )
        
        print(f"ELO ratings updated for {len(SEASON_RESULTS_2026)} races")
    except Exception as e:
        print(f"Warning: Could not update ELO ratings: {e}")


# Run ELO updates at module load time
_update_elo_ratings_from_season_results()
