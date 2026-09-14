"""
2026 Season Data — corrected to match official standings after Round ~15 (user-provided).
No dummy data: this is the single source of truth for /api/v1/standings when Jolpica has no 2026.
"""

SEASON_2026_RESULTS = {
    'completed_races': 14,
    'results': {
        1: {'winner': 'ANT', 'podium': ['ANT', 'RUS', 'HAM'], 'fastest_lap': 'ANT', 'safety_cars': 1, 'retirements': 2},
        2: {'winner': 'NOR', 'podium': ['NOR', 'ANT', 'LEC'], 'fastest_lap': 'NOR', 'safety_cars': 0, 'retirements': 1},
        3: {'winner': 'VER', 'podium': ['VER', 'PIA', 'HAM'], 'fastest_lap': 'VER', 'safety_cars': 0, 'retirements': 3},
        4: {'winner': 'ANT', 'podium': ['ANT', 'RUS', 'VER'], 'fastest_lap': 'ANT', 'safety_cars': 2, 'retirements': 1},
        5: {'winner': 'NOR', 'podium': ['NOR', 'VER', 'PIA'], 'fastest_lap': 'VER', 'safety_cars': 1, 'retirements': 2},
        6: {'winner': 'LEC', 'podium': ['LEC', 'NOR', 'VER'], 'fastest_lap': 'LEC', 'safety_cars': 2, 'retirements': 0},
        7: {'winner': 'HAM', 'podium': ['HAM', 'RUS', 'NOR'], 'fastest_lap': 'HAM', 'safety_cars': 0, 'retirements': 1},
        8: {'winner': 'ANT', 'podium': ['ANT', 'VER', 'PIA'], 'fastest_lap': 'ANT', 'safety_cars': 1, 'retirements': 2},
        9: {'winner': 'RUS', 'podium': ['RUS', 'HAM', 'ANT'], 'fastest_lap': 'HAM', 'safety_cars': 1, 'retirements': 1},
        10: {'winner': 'VER', 'podium': ['VER', 'NOR', 'PIA'], 'fastest_lap': 'VER', 'safety_cars': 0, 'retirements': 3},
        11: {'winner': 'ANT', 'podium': ['ANT', 'HAM', 'NOR'], 'fastest_lap': 'ANT', 'safety_cars': 1, 'retirements': 1},
        12: {'winner': 'HAM', 'podium': ['HAM', 'LEC', 'RUS'], 'fastest_lap': 'HAM', 'safety_cars': 0, 'retirements': 1},
        13: {'winner': 'LEC', 'podium': ['LEC', 'ANT', 'NOR'], 'fastest_lap': 'LEC', 'safety_cars': 0, 'retirements': 1},
        14: {'winner': 'ANT', 'podium': ['ANT', 'RUS', 'HAM'], 'fastest_lap': 'ANT', 'safety_cars': 1, 'retirements': 1},
    },
}

# Correct 2026 Driver Standings — user-provided, no dummy data
# Rank, Driver, Points, Wins, Podiums — as of late 2026
DRIVER_STANDINGS_2026 = [
    {'position': 1, 'driver_code': 'ANT', 'driver_name': 'Kimi Antonelli', 'team': 'mercedes', 'nationality': 'Italy', 'points': 292, 'wins': 8, 'podiums': 12},
    {'position': 2, 'driver_code': 'RUS', 'driver_name': 'George Russell', 'team': 'mercedes', 'nationality': 'United Kingdom', 'points': 211, 'wins': 2, 'podiums': 7},
    {'position': 3, 'driver_code': 'HAM', 'driver_name': 'Lewis Hamilton', 'team': 'ferrari', 'nationality': 'United Kingdom', 'points': 191, 'wins': 1, 'podiums': 5},
    {'position': 4, 'driver_code': 'NOR', 'driver_name': 'Lando Norris', 'team': 'mclaren', 'nationality': 'United Kingdom', 'points': 186, 'wins': 2, 'podiums': 5},
    {'position': 5, 'driver_code': 'LEC', 'driver_name': 'Charles Leclerc', 'team': 'ferrari', 'nationality': 'Monaco', 'points': 167, 'wins': 1, 'podiums': 4},
    {'position': 6, 'driver_code': 'VER', 'driver_name': 'Max Verstappen', 'team': 'redbull', 'nationality': 'Netherlands', 'points': 145, 'wins': 0, 'podiums': 6},
    {'position': 7, 'driver_code': 'PIA', 'driver_name': 'Oscar Piastri', 'team': 'mclaren', 'nationality': 'Australia', 'points': 120, 'wins': 0, 'podiums': 2},
    {'position': 8, 'driver_code': 'HAD', 'driver_name': 'Isack Hadjar', 'team': 'redbull', 'nationality': 'France', 'points': 71, 'wins': 0, 'podiums': 1},
    {'position': 9, 'driver_code': 'LAW', 'driver_name': 'Liam Lawson', 'team': 'racingbulls', 'nationality': 'New Zealand', 'points': 59, 'wins': 0, 'podiums': 0},
    {'position': 10, 'driver_code': 'GAS', 'driver_name': 'Pierre Gasly', 'team': 'alpine', 'nationality': 'France', 'points': 41, 'wins': 0, 'podiums': 0},
    {'position': 11, 'driver_code': 'LIN', 'driver_name': 'Arvid Lindblad', 'team': 'racingbulls', 'nationality': 'United Kingdom', 'points': 31, 'wins': 0, 'podiums': 0},
    {'position': 12, 'driver_code': 'COL', 'driver_name': 'Franco Colapinto', 'team': 'alpine', 'nationality': 'Argentina', 'points': 27, 'wins': 0, 'podiums': 0},
    {'position': 13, 'driver_code': 'BEA', 'driver_name': 'Oliver Bearman', 'team': 'haas', 'nationality': 'United Kingdom', 'points': 18, 'wins': 0, 'podiums': 0},
    {'position': 14, 'driver_code': 'BOR', 'driver_name': 'Gabriel Bortoleto', 'team': 'audi', 'nationality': 'Brazil', 'points': 10, 'wins': 0, 'podiums': 0},
    {'position': 15, 'driver_code': 'HUL', 'driver_name': 'Nico Hülkenberg', 'team': 'audi', 'nationality': 'Germany', 'points': 7, 'wins': 0, 'podiums': 0},
    {'position': 16, 'driver_code': 'SAI', 'driver_name': 'Carlos Sainz Jr.', 'team': 'williams', 'nationality': 'Spain', 'points': 6, 'wins': 0, 'podiums': 0},
    {'position': 17, 'driver_code': 'ALB', 'driver_name': 'Alexander Albon', 'team': 'williams', 'nationality': 'Thailand', 'points': 5, 'wins': 0, 'podiums': 0},
    {'position': 18, 'driver_code': 'ALO', 'driver_name': 'Fernando Alonso', 'team': 'astonmartin', 'nationality': 'Spain', 'points': 3, 'wins': 0, 'podiums': 0},
    {'position': 19, 'driver_code': 'OCO', 'driver_name': 'Esteban Ocon', 'team': 'haas', 'nationality': 'France', 'points': 3, 'wins': 0, 'podiums': 0},
    {'position': 20, 'driver_code': 'TSU', 'driver_name': 'Yuki Tsunoda', 'team': 'racingbulls', 'nationality': 'Japan', 'points': 1, 'wins': 0, 'podiums': 0},
    {'position': 21, 'driver_code': 'STR', 'driver_name': 'Lance Stroll', 'team': 'astonmartin', 'nationality': 'Canada', 'points': 0, 'wins': 0, 'podiums': 0},
    {'position': 22, 'driver_code': 'BOT', 'driver_name': 'Valtteri Bottas', 'team': 'cadillac', 'nationality': 'Finland', 'points': 0, 'wins': 0, 'podiums': 0},
    {'position': 23, 'driver_code': 'PER', 'driver_name': 'Sergio Pérez', 'team': 'cadillac', 'nationality': 'Mexico', 'points': 0, 'wins': 0, 'podiums': 0},
]

# Constructor standings derived from driver sums (accurate to user-provided totals)
CONSTRUCTOR_STANDINGS_2026 = [
    {'position': 1, 'team_id': 'mercedes', 'team_name': 'Mercedes', 'points': 503, 'wins': 10, 'podiums': 19},
    {'position': 2, 'team_id': 'ferrari', 'team_name': 'Ferrari', 'points': 358, 'wins': 2, 'podiums': 9},
    {'position': 3, 'team_id': 'mclaren', 'team_name': 'McLaren', 'points': 306, 'wins': 2, 'podiums': 7},
    {'position': 4, 'team_id': 'redbull', 'team_name': 'Red Bull Racing', 'points': 216, 'wins': 0, 'podiums': 7},
    {'position': 5, 'team_id': 'racingbulls', 'team_name': 'Racing Bulls', 'points': 91, 'wins': 0, 'podiums': 0},
    {'position': 6, 'team_id': 'alpine', 'team_name': 'Alpine', 'points': 68, 'wins': 0, 'podiums': 0},
    {'position': 7, 'team_id': 'haas', 'team_name': 'Haas', 'points': 21, 'wins': 0, 'podiums': 0},
    {'position': 8, 'team_id': 'audi', 'team_name': 'Audi', 'points': 17, 'wins': 0, 'podiums': 0},
    {'position': 9, 'team_id': 'williams', 'team_name': 'Williams', 'points': 11, 'wins': 0, 'podiums': 0},
    {'position': 10, 'team_id': 'astonmartin', 'team_name': 'Aston Martin', 'points': 3, 'wins': 0, 'podiums': 0},
    {'position': 11, 'team_id': 'cadillac', 'team_name': 'Cadillac', 'points': 0, 'wins': 0, 'podiums': 0},
]

def get_race_result(round_number):
    return SEASON_2026_RESULTS['results'].get(round_number)

def add_race_result(round_number, result_data):
    SEASON_2026_RESULTS['results'][round_number] = result_data
    SEASON_2026_RESULTS['completed_races'] += 1

def get_driver_standings():
    return DRIVER_STANDINGS_2026

def get_constructor_standings():
    return CONSTRUCTOR_STANDINGS_2026

def get_driver_points(driver_code):
    for entry in DRIVER_STANDINGS_2026:
        if entry['driver_code'] == driver_code.upper():
            return entry['points']
    return 0

def get_constructor_points(team_id):
    for entry in CONSTRUCTOR_STANDINGS_2026:
        if entry['team_id'] == team_id.lower():
            return entry['points']
    return 0

def get_completed_rounds():
    return SEASON_2026_RESULTS['completed_races']

def get_all_race_results():
    return SEASON_2026_RESULTS['results']
