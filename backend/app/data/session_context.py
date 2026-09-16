"""Translate external F1 sources into small, safe model inputs."""
from __future__ import annotations
import datetime as dt
from typing import Any, Dict

from backend.app.config.settings import settings
from backend.app.config.team_driver_lineup_2026 import get_all_drivers
from backend.app.data.calendar_2026 import get_race_by_id
from backend.app.data.pipeline import DataPipeline, DataProvenance
from backend.app.data.pipeline_config import PipelineConfig


# Initialize the data pipeline with configuration
pipeline_config = PipelineConfig.get_pipeline_config()
data_pipeline = DataPipeline()


def _payload(response: Dict[str, Any]) -> Any:
    return response.get('data') if isinstance(response, dict) else None


def _standings_rows(payload: Any) -> list[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    return (payload.get('MRData', {}).get('StandingsTable', {})
            .get('StandingsLists', [{}])[0].get('DriverStandings', []))


def _qualifying_rows(payload: Any) -> list[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    return payload.get('MRData', {}).get('RaceTable', {}).get('Races', [{}])[0].get('QualifyingResults', [])


def build_session_context(race_id: str, session_type: str) -> Dict[str, Any]:
    """Return live-derived strength/grid inputs and transparent provenance."""
    race = get_race_by_id(race_id)
    if not race or not race.get('round'):
        return {'strength_adjustments': {}, 'grid_positions': {}, 'sources': []}

    sources: list[str] = []
    strength_adjustments: Dict[str, float] = {}
    grid_positions: Dict[str, int] = {}
    # Built for a Jolpica->code mapping this function does not yet use. Kept and
    # marked rather than deleted so the wiring gap is explicit.
    _roster_by_number = {str(d['number']): d['code'] for d in get_all_drivers()}
    try:
        from backend.app.data.jolpica_client import JolpicaClient
        client = JolpicaClient()
        
        # Get and process driver standings
        standings = client.get_driver_standings(settings.SEASON_YEAR)
        _standings_payload = _payload(standings)  # built for a mapping this fn does not yet use
        
        # Create provenance for standings data
        standings_provenance = DataProvenance(
            source=f"championship standings ({standings.get('source', 'unknown')})",
            timestamp=dt.datetime.now(),
            cache_status=standings.get('source', 'unknown')
        )
        
        try:
            normalized_standings = data_pipeline.process(
                'standings', 
                _payload(standings), 
                standings_provenance
            )
            
            for code, stats in normalized_standings['data'].items():
                try:
                    if code and isinstance(stats['position'], int):
                        strength_adjustments[str(code).upper()] = max(-0.08, 0.10 - stats['position'] * 0.008)
                except (TypeError, ValueError):
                    continue
            if normalized_standings['data']:
                sources.append(normalized_standings['provenance']['source'])
        except Exception as e:
            sources.append(f"standings validation failed: {str(e)}")

        # Only get qualifying data for races
        if session_type == 'race':
            qualifying = client.get_qualifying_result(settings.SEASON_YEAR, race['round'])
            _qualifying_payload = _payload(qualifying)  # see note above
            
            # Create provenance for qualifying data
            qualifying_provenance = DataProvenance(
                source=f"published qualifying ({qualifying.get('source', 'unknown')})",
                timestamp=dt.datetime.now(),
                cache_status=qualifying.get('source', 'unknown')
            )
            
            try:
                normalized_qualifying = data_pipeline.process(
                    'grid', 
                    _payload(qualifying), 
                    qualifying_provenance
                )
                
                for code, position in normalized_qualifying['data'].items():
                    try:
                        position = int(position)
                    except (TypeError, ValueError):
                        continue
                    if code:
                        grid_positions[str(code).upper()] = position
                if grid_positions:
                    sources.append(normalized_qualifying['provenance']['source'])
            except Exception as e:
                sources.append(f"qualifying validation failed: {str(e)}")
    except Exception as exc:
        sources.append(f"external data unavailable: {type(exc).__name__}")
        if settings.DEBUG:
            raise

    return {'strength_adjustments': strength_adjustments, 'grid_positions': grid_positions, 'sources': sources}
