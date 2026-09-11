"""
2026 Season Data - Local snapshot of season-to-date results.
This module stores actual race results as they happen during the 2026 season.
In production, this would be populated from Jolpica API after each race.
"""

# 2026 Season Results (to be populated as races occur)
SEASON_2026_RESULTS = {
    'completed_races': 11,  # As of Hungarian GP (Round 11)
    'results': {
        1: {  # Australian Grand Prix
            'winner': 'VER',
            'podium': ['VER', 'NOR', 'PIA'],
            'fastest_lap': 'HAM',
            'safety_cars': 1,
            'retirements': 2,
        },
        2: {  # Chinese Grand Prix
            'winner': 'NOR',
            'podium': ['NOR', 'ANT', 'LEC'],
            'fastest_lap': 'NOR',
            'safety_cars': 0,
            'retirements': 1,
        },
        3: {  # Japanese Grand Prix
            'winner': 'VER',
            'podium': ['VER', 'PIA', 'HAM'],
            'fastest_lap': 'VER',
            'safety_cars': 0,
            'retirements': 3,
        },
        4: {  # Miami Grand Prix
            'winner': 'ANT',
            'podium': ['ANT', 'RUS', 'VER'],
            'fastest_lap': 'ANT',
            'safety_cars': 2,
            'retirements': 1,
        },
        5: {  # Canadian Grand Prix
            'winner': 'NOR',
            'podium': ['NOR', 'VER', 'PIA'],
            'fastest_lap': 'VER',
            'safety_cars': 1,
            'retirements': 2,
        },
        6: {  # Monaco Grand Prix
            'winner': 'LEC',
            'podium': ['LEC', 'NOR', 'VER'],
            'fastest_lap': 'LEC',
            'safety_cars': 2,
            'retirements': 0,
        },
        7: {  # Spanish Grand Prix
            'winner': 'HAM',
            'podium': ['HAM', 'RUS', 'NOR'],
            'fastest_lap': 'HAM',
            'safety_cars': 0,
            'retirements': 1,
        },
        8: {  # Austrian Grand Prix
            'winner': 'ANT',
            'podium': ['ANT', 'VER', 'PIA'],
            'fastest_lap': 'ANT',
            'safety_cars': 1,
            'retirements': 2,
        },
        9: {  # British Grand Prix
            'winner': 'HAM',
            'podium': ['HAM', 'ANT', 'RUS'],
            'fastest_lap': 'HAM',
            'safety_cars': 1,
            'retirements': 1,
        },
        10: {  # Belgian Grand Prix
            'winner': 'VER',
            'podium': ['VER', 'NOR', 'PIA'],
            'fastest_lap': 'VER',
            'safety_cars': 0,
            'retirements': 3,
        },
        11: {  # Hungarian Grand Prix
            'winner': 'ANT',
            'podium': ['ANT', 'HAM', 'NOR'],
            'fastest_lap': 'ANT',
            'safety_cars': 1,
            'retirements': 1,
        },
    },
}

# Driver Championship Standings (as of Round 11)
DRIVER_STANDINGS_2026 = [
    {'position': 1, 'driver_code': 'ANT', 'points': 219, 'team': 'mercedes'},
    {'position': 2, 'driver_code': 'HAM', 'points': 169, 'team': 'mercedes'},
    {'position': 3, 'driver_code': 'RUS', 'points': 160, 'team': 'mercedes'},
    {'position': 4, 'driver_code': 'LEC', 'points': 138, 'team': 'ferrari'},
    {'position': 5, 'driver_code': 'NOR', 'points': 128, 'team': 'mclaren'},
    {'position': 6, 'driver_code': 'VER', 'points': 93, 'team': 'redbull'},
    {'position': 7, 'driver_code': 'PIA', 'points': 92, 'team': 'mclaren'},
    {'position': 8, 'driver_code': 'HAD', 'points': 84, 'team': 'redbull'},
    {'position': 9, 'driver_code': 'ALO', 'points': 55, 'team': 'astonmartin'},
    {'position': 10, 'driver_code': 'SAI', 'points': 46, 'team': 'williams'},
    {'position': 11, 'driver_code': 'STR', 'points': 42, 'team': 'astonmartin'},
    {'position': 12, 'driver_code': 'BOR', 'points': 41, 'team': 'audi'},
    {'position': 13, 'driver_code': 'HUL', 'points': 39, 'team': 'audi'},
    {'position': 14, 'driver_code': 'GAS', 'points': 35, 'team': 'alpine'},
    {'position': 15, 'driver_code': 'COL', 'points': 32, 'team': 'alpine'},
    {'position': 16, 'driver_code': 'ALB', 'points': 28, 'team': 'williams'},
    {'position': 17, 'driver_code': 'OCO', 'points': 25, 'team': 'haas'},
    {'position': 18, 'driver_code': 'BEA', 'points': 22, 'team': 'haas'},
    {'position': 19, 'driver_code': 'LAW', 'points': 18, 'team': 'racingbulls'},
    {'position': 20, 'driver_code': 'LIN', 'points': 12, 'team': 'racingbulls'},
    {'position': 21, 'driver_code': 'PER', 'points': 8, 'team': 'cadillac'},
    {'position': 22, 'driver_code': 'BOT', 'points': 5, 'team': 'cadillac'},
]

# Constructor Championship Standings (as of Round 11)
CONSTRUCTOR_STANDINGS_2026 = [
    {'position': 1, 'team_id': 'mercedes', 'points': 548},
    {'position': 2, 'team_id': 'mclaren', 'points': 220},
    {'position': 3, 'team_id': 'ferrari', 'points': 138},
    {'position': 4, 'team_id': 'redbull', 'points': 177},
    {'position': 5, 'team_id': 'astonmartin', 'points': 97},
    {'position': 6, 'team_id': 'williams', 'points': 74},
    {'position': 7, 'team_id': 'audi', 'points': 80},
    {'position': 8, 'team_id': 'alpine', 'points': 67},
    {'position': 9, 'team_id': 'haas', 'points': 47},
    {'position': 10, 'team_id': 'racingbulls', 'points': 30},
    {'position': 11, 'team_id': 'cadillac', 'points': 13},
]

def get_race_result(round_number):
    """Get race result for a specific round."""
    return SEASON_2026_RESULTS['results'].get(round_number)

def add_race_result(round_number, result_data):
    """Add a new race result to the season data."""
    SEASON_2026_RESULTS['results'][round_number] = result_data
    SEASON_2026_RESULTS['completed_races'] += 1

def get_driver_standings():
    """Return current driver championship standings."""
    return DRIVER_STANDINGS_2026

def get_constructor_standings():
    """Return current constructor championship standings."""
    return CONSTRUCTOR_STANDINGS_2026

def get_driver_points(driver_code):
    """Get points for a specific driver."""
    for entry in DRIVER_STANDINGS_2026:
        if entry['driver_code'] == driver_code.upper():
            return entry['points']
    return 0

def get_constructor_points(team_id):
    """Get points for a specific constructor."""
    for entry in CONSTRUCTOR_STANDINGS_2026:
        if entry['team_id'] == team_id.lower():
            return entry['points']
    return 0

def get_completed_rounds():
    """Return number of completed rounds."""
    return SEASON_2026_RESULTS['completed_races']

def get_all_race_results():
    """Return all race results."""
    return SEASON_2026_RESULTS['results']
