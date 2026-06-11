"""
2026 F1 Season Data — Results and Standings.

Contains race results, driver standings, and constructor standings
for the 2026 season. Used for championship tracking and historical analysis.

FastF1 Integration: Can now load results from FastF1 instead of hardcoded values.
"""

import logging
from typing import List, Dict, Any, DefaultDict
from collections import defaultdict

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


# Define constructor mapping for all drivers
CONSTRUCTOR_MAPPING = {
    "antonelli": "mercedes",
    "hamilton": "ferrari",  
    "verstappen": "red_bull",
    "leclerc": "ferrari",
    "norris": "mclaren",
    "russell": "mercedes",
    "piastri": "mclaren",
    "sainz": "williams",
    "perez": "cadillac",  
    "alonso": "aston_martin",
    "stroll": "aston_martin",
    "ocon": "haas",  
    "hadjar": "red_bull",
    "colapinto": "alpine",  
    "lawson": "rb",  
    "gasly": "alpine",
    "bearman": "haas",
    "hulkenberg": "audi",  
    "bortoleto": "audi",  
    "albon": "williams",
    "bottas": "cadillac", 
    "lindblad": "rb",  
}


def compute_standings_from_results(
    results: list,
    constructor_mapping: dict,
) -> tuple:
    """
    Single source of truth: derive standings from race results.
    
    Args:
        results: List of race result dictionaries
        constructor_mapping: Dict mapping driver_id to constructor_id
    
    Returns:
        Tuple of (driver_standings, constructor_standings)
    """
    POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
    SPRINT = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

    driver_pts: DefaultDict[str, float] = defaultdict(float)
    driver_wins: DefaultDict[str, int] = defaultdict(int)
    constructor_pts: DefaultDict[str, float] = defaultdict(float)

    for race in results:
        pts_map = SPRINT if race.get("sprint") else POINTS
        for r in race["results"]:
            driver = r["driver"]
            pos = r["position"]
            pts = pts_map.get(pos, 0)
            
            driver_pts[driver] += pts
            constructor_pts[constructor_mapping.get(driver, "unknown")] += pts
            if pos == 1:
                driver_wins[driver] += 1

    driver_standings = [
        {"position": i + 1, "driver": d, "points": p, "wins": driver_wins[d]}
        for i, (d, p) in enumerate(
            sorted(driver_pts.items(), key=lambda x: x[1], reverse=True)
        )
    ]
    constructor_standings = [
        {"position": i + 1, "team": t, "points": p}
        for i, (t, p) in enumerate(
            sorted(constructor_pts.items(), key=lambda x: x[1], reverse=True)
        )
    ]
    return driver_standings, constructor_standings


# Derive standings from results - single source of truth
DRIVER_STANDINGS_AFTER_R5, CONSTRUCTOR_STANDINGS_AFTER_R5 = (
    compute_standings_from_results(SEASON_RESULTS_2026, CONSTRUCTOR_MAPPING)
)


# Stable aliases for use in API and other modules (QUALITY-02)
CURRENT_DRIVER_STANDINGS = DRIVER_STANDINGS_AFTER_R5
CURRENT_CONSTRUCTOR_STANDINGS = CONSTRUCTOR_STANDINGS_AFTER_R5


def get_season_results(season: int = 2026) -> List[Dict[str, Any]]:
    """
    Return season race results, using FastF1 when available.
    """
    if FASTF1_AVAILABLE:
        try:
            return load_season_results_from_fastf1(season)
        except Exception:
            pass
    return SEASON_RESULTS_2026


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
    season_results = get_season_results(2026)

    # Look through the season results to find races where the driver participated
    for race in reversed(season_results):
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


def get_driver_standings(season: int = 2026) -> List[Dict[str, Any]]:
    """Return driver standings computed from the current season data."""
    season_results = get_season_results(season)
    standings, _ = compute_standings_from_results(season_results, CONSTRUCTOR_MAPPING)
    return standings


def get_constructor_standings(season: int = 2026) -> List[Dict[str, Any]]:
    """Return constructor standings computed from the current season data."""
    season_results = get_season_results(season)
    _, standings = compute_standings_from_results(season_results, CONSTRUCTOR_MAPPING)
    return standings


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
    "get_season_results",
    "get_driver_last_n_results",
    "get_driver_standings",
    "get_constructor_standings",
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
