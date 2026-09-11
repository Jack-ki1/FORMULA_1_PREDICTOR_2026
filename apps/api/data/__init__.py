"""
Data module for F1 Predictor 2026.
"""
from data.calendar_2026 import (
    CALENDAR_2026,
    get_active_calendar,
    get_race_by_id,
    get_race_by_round,
    get_upcoming_races,
    get_completed_races,
    get_sprint_races,
    get_total_rounds,
    get_next_race,
    get_circuit_names,
)
from data.driver_data import (
    get_driver_bios,
    get_driver_bio,
    get_enhanced_driver_data,
    get_all_enhanced_drivers,
)
from data.team_data import (
    get_team_stats,
    get_team_stat,
    get_enhanced_team_data,
    get_all_enhanced_teams,
    get_team_power_rankings,
)
from data.circuit_data import (
    CIRCUITS,
    get_circuit_by_name,
    get_circuit_by_id,
    get_all_circuits,
    get_circuit_characteristics,
    get_circuit_type,
)
from data.season_2026 import (
    SEASON_2026_RESULTS,
    DRIVER_STANDINGS_2026,
    CONSTRUCTOR_STANDINGS_2026,
    get_race_result,
    add_race_result,
    get_driver_standings,
    get_constructor_standings,
    get_driver_points,
    get_constructor_points,
    get_completed_rounds,
    get_all_race_results,
)
from data.api_client import APIClient
from data.jolpica_client import JolpicaClient
from data.openf1_client import OpenF1Client
from data.fastf1_integration import FastF1Integration
from data.huggingface_dataset import HuggingFaceDataset
from data.live_updater import (
    LiveUpdater,
    live_updater,
    start_live_updater,
    stop_live_updater,
    force_live_update,
)

__all__ = [
    'CALENDAR_2026',
    'get_active_calendar',
    'get_race_by_id',
    'get_race_by_round',
    'get_upcoming_races',
    'get_completed_races',
    'get_sprint_races',
    'get_total_rounds',
    'get_next_race',
    'get_circuit_names',
    'get_driver_bios',
    'get_driver_bio',
    'get_enhanced_driver_data',
    'get_all_enhanced_drivers',
    'get_team_stats',
    'get_team_stat',
    'get_enhanced_team_data',
    'get_all_enhanced_teams',
    'get_team_power_rankings',
    'CIRCUITS',
    'get_circuit_by_name',
    'get_circuit_by_id',
    'get_all_circuits',
    'get_circuit_characteristics',
    'get_circuit_type',
    'SEASON_2026_RESULTS',
    'DRIVER_STANDINGS_2026',
    'CONSTRUCTOR_STANDINGS_2026',
    'get_race_result',
    'add_race_result',
    'get_driver_standings',
    'get_constructor_standings',
    'get_driver_points',
    'get_constructor_points',
    'get_completed_rounds',
    'get_all_race_results',
    'APIClient',
    'JolpicaClient',
    'OpenF1Client',
    'FastF1Integration',
    'HuggingFaceDataset',
    'LiveUpdater',
    'live_updater',
    'start_live_updater',
    'stop_live_updater',
    'force_live_update',
]
