"""
2026 F1 Team and Driver Lineup.
Single source of truth for 11 teams / 22 drivers with their attributes.
Strength values calibrated against REAL 2026 championship standings after Round 11.
"""
from backend.app.config.constants import TEAM_COLORS

# 2026 Team and Driver Lineup
# Strength values based on Round 11 2026 standings:
# Antonelli 219pts, Hamilton 169, Russell 160, Leclerc 138, Norris 128, 
# Verstappen 93, Piastri 92, Hadjar 84 (source checked 28 Jul 2026)
# Mapped via strength = 35 + 62·sqrt(points / 219)
TEAMS_2026 = [
    {
        'id': 'mclaren',
        'name': 'McLaren',
        'color': TEAM_COLORS['mclaren'],
        'drivers': [
            {
                'code': 'NOR',
                'name': 'Lando Norris',
                'number': 4,
                'strength': 82,
                'reliability': 92,
                'wet_skill': 70,
            },
            {
                'code': 'PIA',
                'name': 'Oscar Piastri',
                'number': 81,
                'strength': 75,
                'reliability': 82,
                'wet_skill': 70,
            },
        ],
    },
    {
        'id': 'ferrari',
        'name': 'Ferrari',
        'color': TEAM_COLORS['ferrari'],
        'drivers': [
            {
                'code': 'LEC',
                'name': 'Charles Leclerc',
                'number': 16,
                'strength': 84,
                'reliability': 85,
                'wet_skill': 74,
            },
            {
                'code': 'HAM',
                'name': 'Lewis Hamilton',
                'number': 44,
                'strength': 89,
                'reliability': 84,
                'wet_skill': 88,
            },
        ],
    },
    {
        'id': 'redbull',
        'name': 'Red Bull Racing',
        'color': TEAM_COLORS['redbull'],
        'drivers': [
            {
                'code': 'VER',
                'name': 'Max Verstappen',
                'number': 1,
                'strength': 75,
                'reliability': 88,
                'wet_skill': 90,
            },
            {
                'code': 'HAD',
                'name': 'Isack Hadjar',
                'number': 6,
                'strength': 73,
                'reliability': 80,
                'wet_skill': 60,
            },
        ],
    },
    {
        'id': 'mercedes',
        'name': 'Mercedes',
        'color': TEAM_COLORS['mercedes'],
        'drivers': [
            {
                'code': 'RUS',
                'name': 'George Russell',
                'number': 63,
                'strength': 88,
                'reliability': 90,
                'wet_skill': 75,
            },
            {
                'code': 'ANT',
                'name': 'Kimi Antonelli',
                'number': 12,
                'strength': 97,
                'reliability': 83,
                'wet_skill': 65,
            },
        ],
    },
    {
        'id': 'astonmartin',
        'name': 'Aston Martin',
        'color': TEAM_COLORS['astonmartin'],
        'drivers': [
            {
                'code': 'ALO',
                'name': 'Fernando Alonso',
                'number': 14,
                'strength': 55,
                'reliability': 82,
                'wet_skill': 92,
            },
            {
                'code': 'STR',
                'name': 'Lance Stroll',
                'number': 18,
                'strength': 50,
                'reliability': 78,
                'wet_skill': 68,
            },
        ],
    },
    {
        'id': 'williams',
        'name': 'Williams',
        'color': TEAM_COLORS['williams'],
        'drivers': [
            {
                'code': 'SAI',
                'name': 'Carlos Sainz',
                'number': 55,
                'strength': 46,
                'reliability': 81,
                'wet_skill': 80,
            },
            {
                'code': 'ALB',
                'name': 'Alex Albon',
                'number': 23,
                'strength': 42,
                'reliability': 83,
                'wet_skill': 72,
            },
        ],
    },
    {
        'id': 'audi',
        'name': 'Audi',
        'color': TEAM_COLORS['audi'],
        'drivers': [
            {
                'code': 'HUL',
                'name': 'Nico Hülkenberg',
                'number': 27,
                'strength': 41,
                'reliability': 74,
                'wet_skill': 70,
            },
            {
                'code': 'BOR',
                'name': 'Gabriel Bortoleto',
                'number': 5,
                'strength': 48,
                'reliability': 70,
                'wet_skill': 60,
            },
        ],
    },
    {
        'id': 'alpine',
        'name': 'Alpine',
        'color': TEAM_COLORS['alpine'],
        'drivers': [
            {
                'code': 'GAS',
                'name': 'Pierre Gasly',
                'number': 10,
                'strength': 49,
                'reliability': 76,
                'wet_skill': 74,
            },
            {
                'code': 'COL',
                'name': 'Franco Colapinto',
                'number': 43,
                'strength': 43,
                'reliability': 69,
                'wet_skill': 62,
            },
        ],
    },
    {
        'id': 'haas',
        'name': 'Haas',
        'color': TEAM_COLORS['haas'],
        'drivers': [
            {
                'code': 'OCO',
                'name': 'Esteban Ocon',
                'number': 31,
                'strength': 44,
                'reliability': 77,
                'wet_skill': 71,
            },
            {
                'code': 'BEA',
                'name': 'Oliver Bearman',
                'number': 87,
                'strength': 42,
                'reliability': 73,
                'wet_skill': 63,
            },
        ],
    },
    {
        'id': 'racingbulls',
        'name': 'Racing Bulls',
        'color': TEAM_COLORS['racingbulls'],
        'drivers': [
            {
                'code': 'LAW',
                'name': 'Liam Lawson',
                'number': 30,
                'strength': 51,
                'reliability': 75,
                'wet_skill': 68,
            },
            {
                'code': 'LIN',
                'name': 'Arvid Lindblad',
                'number': 41,
                'strength': 45,
                'reliability': 68,
                'wet_skill': 55,
            },
        ],
    },
    {
        'id': 'cadillac',
        'name': 'Cadillac',
        'color': TEAM_COLORS['cadillac'],
        'drivers': [
            {
                'code': 'PER',
                'name': 'Sergio Pérez',
                'number': 11,
                'strength': 41,
                'reliability': 66,
                'wet_skill': 66,
            },
            {
                'code': 'BOT',
                'name': 'Valtteri Bottas',
                'number': 77,
                'strength': 39,
                'reliability': 70,
                'wet_skill': 69,
            },
        ],
    },
]

def get_all_teams():
    """Return all teams."""
    return TEAMS_2026

def get_team_by_id(team_id):
    """Get team by ID."""
    for team in TEAMS_2026:
        if team['id'] == team_id.lower():
            return team
    return None

def get_all_drivers():
    """Return flat list of all drivers with team information."""
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
    """Get driver by code."""
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
    """Get all drivers for a specific team."""
    team = get_team_by_id(team_id)
    if team:
        return team['drivers']
    return []

def get_driver_count():
    """Return total number of drivers."""
    return len(get_all_drivers())

def get_team_count():
    """Return total number of teams."""
    return len(TEAMS_2026)
