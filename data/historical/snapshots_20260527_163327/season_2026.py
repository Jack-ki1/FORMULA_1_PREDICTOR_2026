"""
2026 F1 Season — Race Results Database.

Only results that occurred BEFORE the prediction cutoff are stored here.
Adding post-race results after each race keeps the system up to date
without contaminating future predictions.
"""

from datetime import date

SEASON_RESULTS_2026: list = [
    {
        "round": 1,
        "circuit": "australia",
        "name": "Australian Grand Prix",
        "date": "2026-03-08",
        "sprint": False,
        "results": [
            {"driver": "russell",    "position": 1, "grid": 2, "points": 25, "dnf": False, "fastest_lap": False},
            {"driver": "antonelli",  "position": 2, "grid": 1, "points": 18, "dnf": False, "fastest_lap": True},
            {"driver": "leclerc",    "position": 3, "grid": 3, "points": 15, "dnf": False, "fastest_lap": False},
            {"driver": "norris",     "position": 4, "grid": 5, "points": 12, "dnf": False, "fastest_lap": False},
            {"driver": "hamilton",   "position": 5, "grid": 4, "points": 10, "dnf": False, "fastest_lap": False},
            {"driver": "piastri",    "position": 6, "grid": 6, "points":  8, "dnf": False, "fastest_lap": False},
            {"driver": "verstappen", "position": 7, "grid": 8, "points":  6, "dnf": False, "fastest_lap": False},
            {"driver": "bearman",    "position": 8, "grid": 9, "points":  4, "dnf": False, "fastest_lap": False},
            {"driver": "gasly",      "position": 9, "grid": 10,"points":  2, "dnf": False, "fastest_lap": False},
            {"driver": "colapinto",  "position": 10,"grid": 12,"points":  1, "dnf": False, "fastest_lap": False},
        ],
    },
    {
        "round": 2,
        "circuit": "china",
        "name": "Chinese Grand Prix",
        "date": "2026-03-15",
        "sprint": True,
        "results": [
            {"driver": "antonelli",  "position": 1, "grid": 1, "points": 25, "dnf": False, "fastest_lap": True},
            {"driver": "russell",    "position": 2, "grid": 2, "points": 18, "dnf": False, "fastest_lap": False},
            {"driver": "hamilton",   "position": 3, "grid": 4, "points": 15, "dnf": False, "fastest_lap": False},
            {"driver": "leclerc",    "position": 4, "grid": 3, "points": 12, "dnf": False, "fastest_lap": False},
            {"driver": "norris",     "position": 5, "grid": 6, "points": 10, "dnf": False, "fastest_lap": False},
            {"driver": "piastri",    "position": 6, "grid": 5, "points":  8, "dnf": False, "fastest_lap": False},
            {"driver": "verstappen", "position": 7, "grid": 8, "points":  6, "dnf": False, "fastest_lap": False},
            {"driver": "bearman",    "position": 8, "grid": 7, "points":  4, "dnf": False, "fastest_lap": False},
            {"driver": "gasly",      "position": 9, "grid": 11,"points":  2, "dnf": False, "fastest_lap": False},
            {"driver": "lawson",     "position": 10,"grid": 9, "points":  1, "dnf": False, "fastest_lap": False},
        ],
    },
    {
        "round": 3,
        "circuit": "japan",
        "name": "Japanese Grand Prix",
        "date": "2026-04-06",
        "sprint": False,
        "results": [
            {"driver": "antonelli",  "position": 1, "grid": 1, "points": 26, "dnf": False, "fastest_lap": True},
            {"driver": "piastri",    "position": 2, "grid": 6, "points": 18, "dnf": False, "fastest_lap": False},
            {"driver": "leclerc",    "position": 3, "grid": 4, "points": 15, "dnf": False, "fastest_lap": False},
            {"driver": "hamilton",   "position": 4, "grid": 5, "points": 12, "dnf": False, "fastest_lap": False},
            {"driver": "norris",     "position": 5, "grid": 3, "points": 10, "dnf": False, "fastest_lap": False},
            {"driver": "russell",    "position": 6, "grid": 2, "points":  8, "dnf": False, "fastest_lap": False},
            {"driver": "bearman",    "position": 7, "grid": 8, "points":  6, "dnf": False, "fastest_lap": False},
            {"driver": "verstappen", "position": 8, "grid": 7, "points":  4, "dnf": False, "fastest_lap": False},
            {"driver": "colapinto",  "position": 9, "grid": 11,"points":  2, "dnf": False, "fastest_lap": False},
            {"driver": "lawson",     "position": 10,"grid": 10,"points":  1, "dnf": False, "fastest_lap": False},
        ],
    },
    {
        "round": 4,
        "circuit": "miami",
        "name": "Miami Grand Prix",
        "date": "2026-05-03",
        "sprint": True,
        "results": [
            {"driver": "antonelli",  "position": 1, "grid": 1, "points": 25, "dnf": False, "fastest_lap": False},
            {"driver": "norris",     "position": 2, "grid": 3, "points": 18, "dnf": False, "fastest_lap": False},
            {"driver": "piastri",    "position": 3, "grid": 5, "points": 15, "dnf": False, "fastest_lap": True},
            {"driver": "russell",    "position": 4, "grid": 2, "points": 12, "dnf": False, "fastest_lap": False},
            {"driver": "verstappen", "position": 5, "grid": 6, "points": 10, "dnf": False, "fastest_lap": False},
            {"driver": "hamilton",   "position": 6, "grid": 4, "points":  8, "dnf": False, "fastest_lap": False},
            {"driver": "bearman",    "position": 7, "grid": 8, "points":  6, "dnf": False, "fastest_lap": False},
            {"driver": "leclerc",    "position": 8, "grid": 3, "points":  0, "dnf": False, "fastest_lap": False,
             "note": "Originally P3 but 20-second post-race penalty → P8"},
            {"driver": "sainz",      "position": 9, "grid": 11,"points":  2, "dnf": False, "fastest_lap": False},
            {"driver": "albon",      "position": 10,"grid": 14,"points":  1, "dnf": False, "fastest_lap": False},
            {"driver": "colapinto",  "position": 11,"grid": 13,"points":  0, "dnf": False, "fastest_lap": False},
            {"driver": "lawson",     "position": None,"grid": 9,"points": 0, "dnf": True,  "fastest_lap": False,
             "note": "DNF — involved in Gasly incident"},
            {"driver": "gasly",      "position": None,"grid": 10,"points":0, "dnf": True,  "fastest_lap": False,
             "note": "DNF — rollover crash"},
            {"driver": "hadjar",     "position": None,"grid": 12,"points":0, "dnf": True,  "fastest_lap": False,
             "note": "DNF — clumsy crash"},
        ],
    },
]

# ── Championship Standings after Round 4 ──────────────────────────────────────
DRIVER_STANDINGS_AFTER_R4: list = [
    {"position": 1,  "driver": "antonelli",  "points": 100},
    {"position": 2,  "driver": "russell",    "points": 80},
    {"position": 3,  "driver": "leclerc",    "points": 73},  # Improved after Japan podium
    {"position": 4,  "driver": "norris",     "points": 66},  # Lower after Japan result
    {"position": 5,  "driver": "hamilton",   "points": 52},
    {"position": 6,  "driver": "piastri",    "points": 63},  # Improved after Japan podium
    {"position": 7,  "driver": "verstappen", "points": 30},
    {"position": 8,  "driver": "bearman",    "points": 18},
    {"position": 9,  "driver": "gasly",      "points": 14},
    {"position": 10, "driver": "lawson",     "points": 10},
    {"position": 11, "driver": "colapinto",  "points": 11},
    {"position": 12, "driver": "hadjar",     "points": 4},
    {"position": 13, "driver": "lindblad",   "points": 4},
    {"position": 14, "driver": "sainz",      "points": 4},
    {"position": 15, "driver": "bortoleto",  "points": 2},
    {"position": 16, "driver": "albon",      "points": 1},
    {"position": 17, "driver": "ocon",       "points": 1},
    {"position": 18, "driver": "stroll",     "points": 0},
    {"position": 19, "driver": "alonso",     "points": 0},
    {"position": 20, "driver": "perez",      "points": 25},  # New Cadillac driver points
    {"position": 21, "driver": "bottas",     "points": 18},  # New Cadillac driver points
    {"position": 22, "driver": "zhou",       "points": 0},   # Reserve driver
]

CONSTRUCTOR_STANDINGS_AFTER_R4: list = [
    {"position": 1, "team": "mercedes",     "points": 180},
    {"position": 2, "team": "ferrari",      "points": 125},  # Increased with corrected Leclerc points
    {"position": 3, "team": "mclaren",      "points": 129},  # Increased with corrected Piastri points
    {"position": 4, "team": "red_bull",     "points": 34},
    {"position": 5, "team": "alpine",       "points": 25},
    {"position": 6, "team": "haas",         "points": 19},
    {"position": 7, "team": "racing_bulls", "points": 14},
    {"position": 8, "team": "williams",     "points": 5},
    {"position": 9, "team": "audi",         "points": 2},
    {"position": 10,"team": "aston_martin", "points": 0},
    {"position": 11,"team": "cadillac",     "points": 43},   # Combined points for Perez and Bottas
]


def get_driver_last_n_results(driver_id: str, n: int = 4) -> list:
    """Return the last N race results for a driver (most recent first)."""
    results = []
    for race in reversed(SEASON_RESULTS_2026):
        for r in race["results"]:
            if r["driver"] == driver_id:
                results.append({
                    "round": race["round"],
                    "circuit": race["circuit"],
                    "position": r["position"],
                    "grid": r["grid"],
                    "dnf": r["dnf"],
                    "points": r["points"],
                })
                break
        if len(results) >= n:
            break
    return results


def get_constructor_results(team_id: str) -> list:
    """Aggregate results for both drivers in a team."""
    from data.driver_data import get_drivers_for_team
    team_drivers = [d["id"] for d in get_drivers_for_team(team_id)]
    all_results = []
    for driver_id in team_drivers:
        all_results.extend(get_driver_last_n_results(driver_id, n=99))
    return all_results
