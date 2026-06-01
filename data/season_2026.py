"""
2026 F1 Season Data — Results and Standings.

Contains race results, driver standings, and constructor standings
for the 2026 season. Used for championship tracking and historical analysis.

FastF1 Integration: Can now load results from FastF1 instead of hardcoded values.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import FastF1
try:
    from data.fastf1_integration import load_entire_season, FASTF1_AVAILABLE
except ImportError:
    FASTF1_AVAILABLE = False
    logger.warning("FastF1 integration not available.")


# Race results for completed races (R1-R5 as per data)
# NOTE: These can be replaced by FastF1 data using load_season_results_from_fastf1()
SEASON_RESULTS_2026: List[Dict[str, Any]] = [
    {
        "round": 1,
        "circuit": "australia",
        "name": "Australian Grand Prix",
        "date": "2026-03-08",
        "sprint": False,
        "results": [
            {"driver": "russell", "position": 1, "points": 25},
            {"driver": "antonelli", "position": 2, "points": 18},
            {"driver": "leclerc", "position": 3, "points": 15},
            {"driver": "hamilton", "position": 4, "points": 12},
            {"driver": "verstappen", "position": 5, "points": 10},
            {"driver": "bearman", "position": 6, "points": 8},
            {"driver": "lindblad", "position": 7, "points": 6},
            {"driver": "bortoleto", "position": 8, "points": 4},
            {"driver": "colapinto", "position": 9, "points": 2},
            {"driver": "ocon", "position": 10, "points": 1},
        ]
    },

    {
        "round": 2,
        "circuit": "china",
        "name": "Chinese Grand Prix",
        "date": "2026-03-15",
        "sprint": True,
        "results": [
            {"driver": "antonelli", "position": 1, "points": 25},
            {"driver": "russell", "position": 2, "points": 18},
            {"driver": "hamilton", "position": 3, "points": 15},
            {"driver": "leclerc", "position": 4, "points": 12},
            {"driver": "bearman", "position": 5, "points": 10},
            {"driver": "gasly", "position": 6, "points": 8},
            {"driver": "lawson", "position": 7, "points": 6},
            {"driver": "hadjar", "position": 8, "points": 4},
            {"driver": "sainz", "position": 9, "points": 2},
            {"driver": "colapinto", "position": 10, "points": 1},
        ]
    },

    {
        "round": 3,
        "circuit": "japan",
        "name": "Japanese Grand Prix",
        "date": "2026-03-29",
        "sprint": False,
        "results": [
            {"driver": "antonelli", "position": 1, "points": 25},
            {"driver": "piastri", "position": 2, "points": 18},
            {"driver": "leclerc", "position": 3, "points": 15},
            {"driver": "russell", "position": 4, "points": 12},
            {"driver": "verstappen", "position": 5, "points": 10},
            {"driver": "hamilton", "position": 6, "points": 8},
            {"driver": "norris", "position": 7, "points": 6},
            {"driver": "gasly", "position": 8, "points": 4},
            {"driver": "lawson", "position": 9, "points": 2},
            {"driver": "hadjar", "position": 10, "points": 1},
        ]
    },

    {
        "round": 4,
        "circuit": "miami",
        "name": "Miami Grand Prix",
        "date": "2026-05-03",
        "sprint": True,
        "results": [
            {"driver": "antonelli", "position": 1, "points": 25},
            {"driver": "norris", "position": 2, "points": 18},
            {"driver": "piastri", "position": 3, "points": 15},
            {"driver": "russell", "position": 4, "points": 12},
            {"driver": "verstappen", "position": 5, "points": 10},
            {"driver": "hamilton", "position": 6, "points": 8},
            {"driver": "leclerc", "position": 7, "points": 6},
            {"driver": "gasly", "position": 8, "points": 4},
            {"driver": "lawson", "position": 9, "points": 2},
            {"driver": "hadjar", "position": 10, "points": 1},
        ]
    },

    {
        "round": 5,
        "circuit": "canada",
        "name": "Canadian Grand Prix",
        "date": "2026-05-24",
        "sprint": False,
        "results": [
            {"driver": "antonelli", "position": 1, "points": 25},
            {"driver": "hamilton", "position": 2, "points": 18},
            {"driver": "verstappen", "position": 3, "points": 15},
            {"driver": "leclerc", "position": 4, "points": 12},
            {"driver": "hadjar", "position": 5, "points": 10},
            {"driver": "colapinto", "position": 6, "points": 8},
            {"driver": "lawson", "position": 7, "points": 6},
            {"driver": "gasly", "position": 8, "points": 4},
            {"driver": "sainz", "position": 9, "points": 2},
            {"driver": "bearman", "position": 10, "points": 1},
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
            {"driver": "lindblad", "position": 22, "points": 0, "status": "DNS"}
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
    "hamilton": "mercedes",  # FIXED: Was incorrectly set to "ferrari"
    "verstappen": "red_bull",
    "leclerc": "ferrari",
    "norris": "mclaren",
    "russell": "mercedes",
    "piastri": "mclaren",
    "sainz": "williams",
    "perez": "red_bull",
    "alonso": "aston_martin",
    "stroll": "aston_martin",
    "ocon": "alpine",
    "hadjar": "red_bull",
    "colapinto": "williams",
    "lawson": "racing_bulls",
    "gasly": "alpine",
    "bearman": "haas",
    "hulkenberg": "haas",
    "bortoleto": "kick_sauber",
    "albon": "williams",
    "bottas": "kick_sauber",
    "lindblad": "racing_bulls",
    "devries": "kick_sauber",
    "zhou": "kick_sauber",
    "palou": "kick_sauber",
    "magnussen": "kick_sauber",
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
    "get_remaining_races",
    "load_season_results_from_fastf1",  # NEW
    "update_standings_from_fastf1",     # NEW
    "FASTF1_AVAILABLE"                  # NEW
]


# ── FastF1 Integration Functions (NEW) ──────────────────────────────────────────

def load_season_results_from_fastf1(season: int = 2026) -> List[Dict[str, Any]]:
    """
    Load season results from FastF1 instead of hardcoded values.
    
    This function:
    1. Fetches all race results from FastF1 for the specified season
    2. Transforms them into the project's standard format
    3. Returns structured race data with driver positions and points
    
    Args:
        season: Year to load (default: 2026)
    
    Returns:
        List of race dictionaries in the same format as SEASON_RESULTS_2026
    
    Example:
        >>> results = load_season_results_from_fastf1(2026)
        >>> print(f"Loaded {len(results)} races")
        >>> print(f"Round 1 winner: {results[0]['results'][0]['driver']}")
    """
    if not FASTF1_AVAILABLE:
        logger.warning("FastF1 not available. Returning hardcoded results.")
        return SEASON_RESULTS_2026
    
    try:
        # Load entire season from FastF1
        season_data = load_entire_season(season, 'R')
        
        if not season_data:
            logger.warning("No season data available from FastF1.")
            return SEASON_RESULTS_2026
        
        # Transform to project format
        transformed_results = []
        for race in season_data:
            if 'error' in race:
                logger.warning(f"Skipping {race['race_name']}: {race['error']}")
                continue
            
            results_list = []
            for idx, driver_result in race['results'].iterrows():
                results_list.append({
                    "driver": str(driver_result['Abbreviation']).lower(),
                    "position": int(driver_result['Position']),
                    "points": float(driver_result['Points']),
                    "status": str(driver_result['Status']),
                })
            
            transformed_race = {
                "round": race['round'],
                "circuit": race['race_name'].lower().replace(' ', '_').replace('grand_prix', ''),
                "name": race['race_name'],
                "date": str(race['date']),
                "sprint": False,  # Would need separate sprint session load
                "results": results_list,
            }
            transformed_results.append(transformed_race)
        
        logger.info(f"Loaded {len(transformed_results)} races from FastF1")
        return transformed_results
        
    except Exception as e:
        logger.error(f"Failed to load season from FastF1: {e}")
        return SEASON_RESULTS_2026


def update_standings_from_fastf1(season: int = 2026) -> Dict[str, Any]:
    """
    Update driver and constructor standings using FastF1 data.
    
    This function:
    1. Loads race results from FastF1
    2. Calculates driver standings
    3. Calculates constructor standings
    4. Returns both standings dictionaries
    
    Args:
        season: Year to calculate standings for (default: 2026)
    
    Returns:
        Dictionary with:
        - driver_standings: List of driver standings entries
        - constructor_standings: List of constructor standings entries
        - races_processed: Number of races used in calculation
    """
    if not FASTF1_AVAILABLE:
        logger.warning("FastF1 not available. Returning existing standings.")
        return {
            "driver_standings": DRIVER_STANDINGS_AFTER_R5,
            "constructor_standings": CONSTRUCTOR_STANDINGS_AFTER_R5,
            "races_processed": 0,
        }
    
    try:
        # Load results from FastF1
        results = load_season_results_from_fastf1(season)
        
        # Calculate driver points
        driver_points = {}
        driver_wins = {}
        constructor_points = {}
        
        for race in results:
            for result in race['results']:
                driver = result['driver']
                points = result['points']
                
                # Driver points
                driver_points[driver] = driver_points.get(driver, 0) + points
                
                # Count wins
                if result['position'] == 1:
                    driver_wins[driver] = driver_wins.get(driver, 0) + 1
                
                # Constructor points
                team = CONSTRUCTOR_MAPPING.get(driver)
                if team:
                    constructor_points[team] = constructor_points.get(team, 0) + points
        
        # Create driver standings
        driver_standings = []
        sorted_drivers = sorted(driver_points.items(), key=lambda x: x[1], reverse=True)
        for i, (driver, points) in enumerate(sorted_drivers):
            driver_standings.append({
                "position": i + 1,
                "driver": driver,
                "points": points,
                "wins": driver_wins.get(driver, 0),
            })
        
        # Create constructor standings
        constructor_standings = []
        sorted_constructors = sorted(constructor_points.items(), key=lambda x: x[1], reverse=True)
        for i, (team, points) in enumerate(sorted_constructors):
            constructor_standings.append({
                "position": i + 1,
                "team": team,
                "points": points,
            })
        
        result = {
            "driver_standings": driver_standings,
            "constructor_standings": constructor_standings,
            "races_processed": len(results),
        }
        
        logger.info(f"Standings updated from FastF1: {len(results)} races processed")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update standings from FastF1: {e}")
        return {
            "driver_standings": DRIVER_STANDINGS_AFTER_R5,
            "constructor_standings": CONSTRUCTOR_STANDINGS_AFTER_R5,
            "races_processed": 0,
        }
