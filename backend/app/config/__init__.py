"""
Configuration module for F1 Predictor 2026.
"""
from backend.app.config.settings import settings, Settings
from backend.app.config.api_settings import api_settings, APISettings
from backend.app.config.feature_weights import feature_weights, FeatureWeights
from backend.app.config.constants import (
    TEAM_COLORS,
    PIRELLI_COMPOUNDS,
    POINTS_SYSTEM,
    SPRINT_POINTS_SYSTEM,
    TARGETS,
    SESSIONS,
    WEATHER_CONDITIONS,
    DNF_RISK_LEVELS,
    grid_prior_multiplier,
    get_team_color,
    get_compound_color,
    get_points_for_position,
    get_target_info,
    is_valid_target,
    get_all_targets,
)
from backend.app.config.team_driver_lineup_2026 import (
    TEAMS_2026,
    get_all_teams,
    get_team_by_id,
    get_all_drivers,
    get_driver_by_code,
    get_drivers_by_team,
    get_driver_count,
    get_team_count,
)

__all__ = [
    'settings',
    'Settings',
    'api_settings',
    'APISettings',
    'feature_weights',
    'FeatureWeights',
    'TEAM_COLORS',
    'PIRELLI_COMPOUNDS',
    'POINTS_SYSTEM',
    'SPRINT_POINTS_SYSTEM',
    'TARGETS',
    'SESSIONS',
    'WEATHER_CONDITIONS',
    'DNF_RISK_LEVELS',
    'grid_prior_multiplier',
    'get_team_color',
    'get_compound_color',
    'get_points_for_position',
    'get_target_info',
    'is_valid_target',
    'get_all_targets',
    'TEAMS_2026',
    'get_all_teams',
    'get_team_by_id',
    'get_all_drivers',
    'get_driver_by_code',
    'get_drivers_by_team',
    'get_driver_count',
    'get_team_count',
]
