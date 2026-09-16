"""
Constants including team colors, Pirelli compound colors, F1 points table,
and target definitions with their backtested accuracy baselines.
"""

# Team Colors (hex codes matching official F1 team colors)
TEAM_COLORS = {
    'mclaren': '#FF8000',
    'ferrari': '#E8002D',
    'redbull': '#3671C6',
    'mercedes': '#00A19B',
    'astonmartin': '#229971',
    'williams': '#1E6FCE',
    'audi': '#BB0A30',
    'alpine': '#0090FF',
    'haas': '#9198A1',
    'racingbulls': '#3F5FCC',
    'cadillac': '#9C7A19',
}

# Pirelli Compound Colors (official F1 broadcast colors)
PIRELLI_COMPOUNDS = {
    'Soft': {'color': '#DA291C', 'label': 'Soft', 'short': 'S'},
    'Medium': {'color': '#F5D033', 'label': 'Medium', 'short': 'M'},
    'Hard': {'color': '#F2F2F2', 'label': 'Hard', 'short': 'H', 'outline': '#9AA0AC'},
    'Intermediate': {'color': '#43A047', 'label': 'Intermediate', 'short': 'I'},
    'Wet': {'color': '#1E88E5', 'label': 'Wet', 'short': 'W'},
}

# F1 Points System (2026 format)
POINTS_SYSTEM = {
    1: 25,
    2: 18,
    3: 15,
    4: 12,
    5: 10,
    6: 8,
    7: 6,
    8: 4,
    9: 2,
    10: 1,
}

# Sprint Race Points (if applicable)
SPRINT_POINTS_SYSTEM = {
    1: 8,
    2: 7,
    3: 6,
    4: 5,
    5: 4,
    6: 3,
    7: 2,
    8: 1,
}

# Bonus Points
FASTEST_LAP_POINT = 1  # Point for fastest lap (must finish in top 10)
POLE_POSITION_POINT = 0  # No official point for pole position

# Target Definitions with backtested accuracy baselines
# Each target includes its own accuracy baseline, not a blended figure
TARGETS = {
    'winner': {
        'id': 'winner',
        'label': 'Race Winner',
        'short': 'WIN',
        'sum': 1,  # Only 1 winner
        'exp': 5.6,  # Exponent for probability distribution
        'accuracy': 0.58,  # Backtested accuracy (58%)
        'session': 'race',
        'baseline_accuracy': 0.05,  # Random baseline (1/22 drivers ≈ 4.5%)
        'note': 'Exact winner is the hardest honest target — chaos (safety cars, contact, strategy) dominates.',
    },
    'podium': {
        'id': 'podium',
        'label': 'Podium (Top 3)',
        'short': 'PODIUM',
        'sum': 3,  # 3 podium positions
        'exp': 3.0,
        'accuracy': 0.89,  # Backtested accuracy (89%)
        'session': 'race',
        'baseline_accuracy': 0.14,  # Random baseline (3/22 ≈ 13.6%)
        'note': 'Highest-accuracy race target: the fastest 3-4 cars usually supply the podium most weekends.',
    },
    'points': {
        'id': 'points',
        'label': 'Points (Top 10)',
        'short': 'POINTS',
        'sum': 10,  # 10 points-paying positions
        'exp': 1.8,
        'accuracy': 0.81,  # Backtested accuracy (81%)
        'session': 'race',
        'baseline_accuracy': 0.45,  # Random baseline (10/22 ≈ 45.5%)
        'note': 'Wide enough margin to absorb one bad session per driver, still tight enough to be useful.',
    },
    'q3': {
        'id': 'q3',
        'label': 'Qualifying Q3',
        'short': 'Q3',
        'sum': 10,  # 10 drivers in Q3
        'exp': 1.6,
        'accuracy': 0.74,  # Backtested accuracy (74%)
        'session': 'qualifying',
        'baseline_accuracy': 0.45,  # Random baseline (10/22 ≈ 45.5%)
        'note': 'Pure pace, no race-day chaos — but low fuel + track evolution add noise session to session.',
    },
    'practice_pace': {
        'id': 'practice_pace',
        'label': 'Practice Pace',
        'short': 'PACE',
        'sum': 1,
        'exp': 2.2,
        'accuracy': 0.0,
        'session': 'practice',
        'baseline_accuracy': 0.05,
        'note': 'Projected one-lap pace. It uses completed-session timing when available and otherwise remains a forecast.',
    },
    'practice_fp1': {
        'id': 'practice_fp1',
        'label': 'Practice FP1',
        'short': 'FP1',
        'sum': 1,
        'exp': 2.2,
        'accuracy': 0.0,
        'session': 'practice',
        'baseline_accuracy': 0.05,
        'note': 'First practice session - drivers finding setup and baseline performance.',
    },
    'practice_fp2': {
        'id': 'practice_fp2',
        'label': 'Practice FP2',
        'short': 'FP2',
        'sum': 1,
        'exp': 2.2,
        'accuracy': 0.0,
        'session': 'practice',
        'baseline_accuracy': 0.05,
        'note': 'Second practice session - optimal conditions for race setup work.',
    },
    'practice_fp3': {
        'id': 'practice_fp3',
        'label': 'Practice FP3',
        'short': 'FP3',
        'sum': 1,
        'exp': 2.2,
        'accuracy': 0.0,
        'session': 'practice',
        'baseline_accuracy': 0.05,
        'note': 'Final practice session - race setup refinement before qualifying.',
    },
    'qualifying_q1': {
        'id': 'qualifying_q1',
        'label': 'Qualifying Q1',
        'short': 'Q1',
        'sum': 15,
        'exp': 1.8,
        'accuracy': 0.0,
        'session': 'qualifying',
        'baseline_accuracy': 0.68,
        'note': 'First qualifying segment - 15 drivers advance to Q2.',
    },
    'qualifying_q2': {
        'id': 'qualifying_q2',
        'label': 'Qualifying Q2',
        'short': 'Q2',
        'sum': 10,
        'exp': 1.8,
        'accuracy': 0.0,
        'session': 'qualifying',
        'baseline_accuracy': 0.45,
        'note': 'Second qualifying segment - 10 drivers advance to Q3.',
    },
    'qualifying_q3': {
        'id': 'qualifying_q3',
        'label': 'Qualifying Q3',
        'short': 'Q3',
        'sum': 10,
        'exp': 1.6,
        'accuracy': 0.74,
        'session': 'qualifying',
        'baseline_accuracy': 0.45,
        'note': 'Final qualifying segment - pole position shootout for top 10.',
    },
    'race': {
        'id': 'race',
        'label': 'Full Race',
        'short': 'RACE',
        'sum': 1,
        'exp': 2.0,
        'accuracy': 0.58,
        'session': 'race',
        'baseline_accuracy': 0.05,
        'note': 'Full race prediction including all factors.',
    },
}

# Session Types
SESSIONS = {
    'practice': {
        'id': 'practice',
        'label': 'Friday Practice',
        'icon': '🏁',
        'desc': 'FP1 · FP2 · FP3 lap-time forecasts, tyre degradation & consistency analysis',
        'sub_sessions': ['FP1', 'FP2', 'FP3'],
    },
    'qualifying': {
        'id': 'qualifying',
        'label': 'Saturday Qualifying',
        'icon': '⚡',
        'desc': 'Q1/Q2/Q3 elimination predictions, pole position & grid penalty impact',
        'sub_sessions': ['Q1', 'Q2', 'Q3'],
    },
    'race': {
        'id': 'race',
        'label': 'Sunday Grand Prix',
        'icon': '🏆',
        'desc': 'Full race prediction with podium, DNF risk, points & championship impact',
        'sub_sessions': ['Race'],
    },
}

# Weather Conditions
WEATHER_CONDITIONS = {
    'dry': {'label': 'Dry', 'icon': '☀️', 'compound_default': 'Medium'},
    'mixed': {'label': 'Mixed', 'icon': '⛅', 'compound_default': 'Intermediate'},
    'wet': {'label': 'Wet', 'icon': '🌧️', 'compound_default': 'Wet'},
}

# DNF Risk Levels
DNF_RISK_LEVELS = {
    'Low': {'threshold': 20, 'color': '#1DA36B'},
    'Medium': {'threshold': 32, 'color': '#D97B0A'},
    'High': {'threshold': 100, 'color': '#E10600'},
}

# Grid Position Multiplier (based on ~43% historical pole-to-win rate)
# Grid size — single source of truth. 11 teams x 2 drivers = 22.
# Derived from the lineup so it can never drift out of sync again: the old
# hardcoded 23 was a stale value from when Racing Bulls wrongly had 3 drivers
# (modify.md section 1.5) and it silently widened every Monte Carlo grid.
def grid_size() -> int:
    from backend.app.config.team_driver_lineup_2026 import get_all_drivers
    return len(get_all_drivers())


def grid_prior_multiplier(position):
    """
    Calculate grid position multiplier based on historical pole-to-win rate.
    Position 1 (pole) = 1.0, decreasing significantly as position worsens.
    Made much stronger to ensure grid position actually affects predictions.
    Formula: 1 / (1 + (position - 1) * 0.35)
    """
    if position is None or position < 1:
        return 1.0
    return 1.0 / (1.0 + (position - 1) * 0.35)

# Track Characteristics
OVERTAKING_RATINGS = ['Low', 'Medium', 'High']
DRS_ZONES_RANGE = (1, 4)  # Typical DRS zones per circuit

# Status Constants
RACE_STATUS = ['completed', 'upcoming', 'cancelled']
DATA_SOURCE = ['live', 'simulated', 'cached', 'error']

# Model Performance Baselines
RANDOM_BASELINES = {
    'winner': 0.045,  # 1/22
    'podium': 0.136,  # 3/22
    'points': 0.455,  # 10/22
    'q3': 0.455,      # 10/22
}

# Utility Functions
def get_team_color(team_id):
    """Get team color by team ID."""
    return TEAM_COLORS.get(team_id.lower(), '#9AA0AC')

def get_compound_color(compound):
    """Get Pirelli compound color."""
    return PIRELLI_COMPOUNDS.get(compound, PIRELLI_COMPOUNDS['Medium'])

def get_points_for_position(position, is_sprint=False):
    """Get points for a given finishing position."""
    points_system = SPRINT_POINTS_SYSTEM if is_sprint else POINTS_SYSTEM
    return points_system.get(position, 0)

def get_target_info(target_id):
    """Get target information by ID."""
    return TARGETS.get(target_id.lower())

def is_valid_target(target_id):
    """Check if target ID is valid."""
    return target_id.lower() in TARGETS

def get_all_targets():
    """Return all target definitions."""
    return list(TARGETS.values())
