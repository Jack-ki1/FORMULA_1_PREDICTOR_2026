"""
2026 F1 Team and Driver Lineup — recalibrated to correct standings (ANT 292, RUS 211, HAM 191...).
Strengths now linear-balanced (ANT 92 not 97) so Monte Carlo respects grid/manual changes.
"""
from backend.app.config.constants import TEAM_COLORS

# 23 drivers (user-provided correct standings) — includes TSU at RB
TEAMS_2026 = [
    {
        'id': 'mclaren',
        'name': 'McLaren',
        'color': TEAM_COLORS['mclaren'],
        'drivers': [
            {'code': 'NOR', 'name': 'Lando Norris', 'number': 4, 'strength': 85, 'reliability': 92, 'wet_skill': 72},
            {'code': 'PIA', 'name': 'Oscar Piastri', 'number': 81, 'strength': 78, 'reliability': 84, 'wet_skill': 70},
        ],
    },
    {
        'id': 'ferrari',
        'name': 'Ferrari',
        'color': TEAM_COLORS['ferrari'],
        'drivers': [
            {'code': 'LEC', 'name': 'Charles Leclerc', 'number': 16, 'strength': 83, 'reliability': 85, 'wet_skill': 74},
            {'code': 'HAM', 'name': 'Lewis Hamilton', 'number': 44, 'strength': 86, 'reliability': 84, 'wet_skill': 88},
        ],
    },
    {
        'id': 'redbull',
        'name': 'Red Bull Racing',
        'color': TEAM_COLORS['redbull'],
        'drivers': [
            {'code': 'VER', 'name': 'Max Verstappen', 'number': 1, 'strength': 80, 'reliability': 88, 'wet_skill': 90},
            {'code': 'HAD', 'name': 'Isack Hadjar', 'number': 6, 'strength': 72, 'reliability': 80, 'wet_skill': 62},
        ],
    },
    {
        'id': 'mercedes',
        'name': 'Mercedes',
        'color': TEAM_COLORS['mercedes'],
        'drivers': [
            {'code': 'RUS', 'name': 'George Russell', 'number': 63, 'strength': 88, 'reliability': 90, 'wet_skill': 75},
            {'code': 'ANT', 'name': 'Kimi Antonelli', 'number': 12, 'strength': 92, 'reliability': 83, 'wet_skill': 65},
        ],
    },
    {
        'id': 'astonmartin',
        'name': 'Aston Martin',
        'color': TEAM_COLORS['astonmartin'],
        'drivers': [
            {'code': 'ALO', 'name': 'Fernando Alonso', 'number': 14, 'strength': 50, 'reliability': 82, 'wet_skill': 92},
            {'code': 'STR', 'name': 'Lance Stroll', 'number': 18, 'strength': 45, 'reliability': 78, 'wet_skill': 68},
        ],
    },
    {
        'id': 'williams',
        'name': 'Williams',
        'color': TEAM_COLORS['williams'],
        'drivers': [
            {'code': 'SAI', 'name': 'Carlos Sainz Jr.', 'number': 55, 'strength': 52, 'reliability': 81, 'wet_skill': 80},
            {'code': 'ALB', 'name': 'Alexander Albon', 'number': 23, 'strength': 51, 'reliability': 83, 'wet_skill': 72},
        ],
    },
    {
        'id': 'audi',
        'name': 'Audi',
        'color': TEAM_COLORS['audi'],
        'drivers': [
            {'code': 'HUL', 'name': 'Nico Hülkenberg', 'number': 27, 'strength': 54, 'reliability': 74, 'wet_skill': 70},
            {'code': 'BOR', 'name': 'Gabriel Bortoleto', 'number': 5, 'strength': 55, 'reliability': 70, 'wet_skill': 60},
        ],
    },
    {
        'id': 'alpine',
        'name': 'Alpine',
        'color': TEAM_COLORS['alpine'],
        'drivers': [
            {'code': 'GAS', 'name': 'Pierre Gasly', 'number': 10, 'strength': 65, 'reliability': 76, 'wet_skill': 74},
            {'code': 'COL', 'name': 'Franco Colapinto', 'number': 43, 'strength': 60, 'reliability': 69, 'wet_skill': 62},
        ],
    },
    {
        'id': 'haas',
        'name': 'Haas',
        'color': TEAM_COLORS['haas'],
        'drivers': [
            {'code': 'OCO', 'name': 'Esteban Ocon', 'number': 31, 'strength': 50, 'reliability': 77, 'wet_skill': 71},
            {'code': 'BEA', 'name': 'Oliver Bearman', 'number': 87, 'strength': 58, 'reliability': 73, 'wet_skill': 63},
        ],
    },
    {
        'id': 'racingbulls',
        'name': 'Racing Bulls',
        'color': TEAM_COLORS['racingbulls'],
        'drivers': [
            {'code': 'LAW', 'name': 'Liam Lawson', 'number': 30, 'strength': 70, 'reliability': 75, 'wet_skill': 68},
            {'code': 'LIN', 'name': 'Arvid Lindblad', 'number': 41, 'strength': 62, 'reliability': 68, 'wet_skill': 55},
            {'code': 'TSU', 'name': 'Yuki Tsunoda', 'number': 22, 'strength': 48, 'reliability': 72, 'wet_skill': 66},
        ],
    },
    {
        'id': 'cadillac',
        'name': 'Cadillac',
        'color': TEAM_COLORS['cadillac'],
        'drivers': [
            {'code': 'PER', 'name': 'Sergio Pérez', 'number': 11, 'strength': 40, 'reliability': 66, 'wet_skill': 66},
            {'code': 'BOT', 'name': 'Valtteri Bottas', 'number': 77, 'strength': 40, 'reliability': 70, 'wet_skill': 69},
        ],
    },
]

def get_all_teams():
    return TEAMS_2026

def get_team_by_id(team_id):
    for team in TEAMS_2026:
        if team['id'] == team_id.lower():
            return team
    return None

def get_all_drivers():
    drivers = []
    for team in TEAMS_2026:
        for driver in team['drivers']:
            driver_copy = driver.copy()
            driver_copy['team_id'] = team['id']
            driver_copy['team_name'] = team['name']
            driver_copy['team_color'] = team['color']
            drivers.append(driver_copy)
    return drivers

def get_driver_by_code(driver_code):
    for team in TEAMS_2026:
        for driver in team['drivers']:
            if driver['code'] == driver_code.upper():
                driver_copy = driver.copy()
                driver_copy['team_id'] = team['id']
                driver_copy['team_name'] = team['name']
                driver_copy['team_color'] = team['color']
                return driver_copy
    return None

def get_drivers_by_team(team_id):
    team = get_team_by_id(team_id)
    if team:
        return team['drivers']
    return []

def get_driver_count():
    return len(get_all_drivers())

def get_team_count():
    return len(TEAMS_2026)
