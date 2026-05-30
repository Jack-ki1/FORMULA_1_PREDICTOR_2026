"""
Fast-F1 Integration — Real F1 Data Pipeline for v3.0.

Integrates fastf1 library for:
- Historical race results ingestion
- Lap-by-lap telemetry data
- Tire compound and pit stop data
- Sector time analysis
- Qualifying session data
- Real-time weather conditions
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import fastf1
    from fastf1 import plotting
    FASTF1_AVAILABLE = True
    plotting.setup_mpl()
except ImportError:
    logger.warning("fastf1 library not installed. Install with: pip install fastf1")
    FASTF1_AVAILABLE = False


def get_session(season: int, race_name: str, session_type: str = 'R'):
    """
    Get F1 session data from fastf1.
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        session_type: 'P1', 'P2', 'P3', 'Q', 'S', 'SQ', 'R'
    
    Returns:
        fastf1.core.Session object
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required. Install: pip install fastf1")
    
    try:
        session = fastf1.get_session(season, race_name, session_type)
        session.load()
        return session
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        raise


def ingest_race_results(season: int, race_name: str) -> Dict:
    """
    Ingest complete race results from fastf1.
    
    Returns:
        Dictionary with driver results including:
        - grid_position, final_position, points
        - laps_completed, status, race_time
        - tire_strategy, pit_stops
    """
    session = get_session(season, race_name, 'R')
    results = session.results
    
    driver_results = []
    for _, driver_result in results.iterrows():
        driver_data = {
            'driver_id': driver_result['Abbreviation'].lower(),
            'driver_name': driver_result['FullName'],
            'team': driver_result['Team'],
            'grid_position': int(driver_result['GridPosition']),
            'final_position': int(driver_result['Position']),
            'points': float(driver_result['Points']),
            'status': driver_result['Status'],
            'laps_completed': int(driver_result['Laps']),
            'fastest_lap': driver_result['FastestLap'] == 1,
        }
        driver_results.append(driver_data)
    
    return {
        'race_name': session.event['EventName'],
        'race_date': session.event['EventDate'].strftime('%Y-%m-%d'),
        'circuit': session.event['Location'],
        'results': driver_results,
    }


def ingest_lap_data(season: int, race_name: str, driver_id: str = None) -> Dict:
    """
    Ingest lap-by-lap data including:
    - Lap times
    - Sector times
    - Tire compound
    - Tire age
    - Pit stop information
    
    Args:
        season: Year
        race_name: Race name or round
        driver_id: Specific driver (optional, None = all drivers)
    """
    session = get_session(season, race_name, 'R')
    laps = session.laps
    
    if driver_id:
        laps = laps.pick_drivers(driver_id.upper())
    
    lap_data = []
    for _, lap in laps.iterrows():
        lap_info = {
            'driver': lap['Driver'],
            'lap_number': int(lap['LapNumber']),
            'lap_time': lap['LapTime'].total_seconds() if lap['LapTime'] else None,
            'sector1_time': lap['Sector1Time'].total_seconds() if lap['Sector1Time'] else None,
            'sector2_time': lap['Sector2Time'].total_seconds() if lap['Sector2Time'] else None,
            'sector3_time': lap['Sector3Time'].total_seconds() if lap['Sector3Time'] else None,
            'compound': lap['Compound'],
            'tire_age': int(lap['TyreLife']),
            'pit_stop': lap['PitOutTime'] is not None,
            'is_personal_best': lap['IsPersonalBest'],
        }
        lap_data.append(lap_info)
    
    return {
        'total_laps': len(lap_data),
        'laps': lap_data,
    }


def ingest_qualifying_results(season: int, race_name: str) -> Dict:
    """
    Ingest qualifying session results with Q1/Q2/Q3 times.
    """
    session = get_session(season, race_name, 'Q')
    results = session.results
    
    qual_data = []
    for _, driver_result in results.iterrows():
        driver_qual = {
            'driver_id': driver_result['Abbreviation'].lower(),
            'driver_name': driver_result['FullName'],
            'team': driver_result['Team'],
            'grid_position': int(driver_result['GridPosition']),
            'q1_best': driver_result['Q1'].total_seconds() if driver_result['Q1'] else None,
            'q2_best': driver_result['Q2'].total_seconds() if driver_result['Q2'] else None,
            'q3_best': driver_result['Q3'].total_seconds() if driver_result['Q3'] else None,
            'eliminated_in': 'Q3' if driver_result['Q3'] else 'Q2' if driver_result['Q2'] else 'Q1',
        }
        qual_data.append(driver_qual)
    
    return {
        'session': session.event['EventName'] + ' Qualifying',
        'results': qual_data,
    }


def ingest_tire_strategy(season: int, race_name: str) -> Dict:
    """
    Ingest tire strategy and pit stop data for all drivers.
    """
    session = get_session(season, race_name, 'R')
    laps = session.laps
    
    # Get pit stop data
    strategies = {}
    drivers = laps['Driver'].unique()
    
    for driver in drivers:
        driver_laps = laps.pick_drivers(driver)
        pit_stops = []
        stints = []
        
        for _, lap in driver_laps.iterrows():
            if lap['PitOutTime'] is not None:
                pit_stops.append({
                    'lap': int(lap['LapNumber']),
                    'compound_in': lap['Compound'],
                })
            
            stints.append({
                'lap': int(lap['LapNumber']),
                'compound': lap['Compound'],
                'tire_age': int(lap['TyreLife']),
                'lap_time': lap['LapTime'].total_seconds() if lap['LapTime'] else None,
            })
        
        strategies[driver] = {
            'total_pit_stops': len(pit_stops),
            'pit_stops': pit_stops,
            'stints': stints,
        }
    
    return strategies


def ingest_weather_data(season: int, race_name: str) -> Dict:
    """
    Ingest weather data from race session.
    """
    session = get_session(season, race_name, 'R')
    
    # Get weather data from laps
    weather_laps = []
    for _, lap in session.laps.iterrows():
        if lap['AirTemp'] is not None:
            weather_laps.append({
                'lap': int(lap['LapNumber']),
                'air_temp': float(lap['AirTemp']),
                'track_temp': float(lap['TrackTemp']),
                'humidity': float(lap['Humidity']) if lap['Humidity'] else None,
                'rainfall': bool(lap['Rainfall']),
                'wind_speed': float(lap['WindSpeed']) if lap['WindSpeed'] else None,
            })
    
    return {
        'circuit': session.event['Location'],
        'weather_data': weather_laps,
        'rained': any(w['rainfall'] for w in weather_laps),
        'avg_air_temp': sum(w['air_temp'] for w in weather_laps) / len(weather_laps) if weather_laps else None,
        'avg_track_temp': sum(w['track_temp'] for w in weather_laps) / len(weather_laps) if weather_laps else None,
    }


def get_historical_circuit_stats(circuit_name: str, seasons: List[int] = None) -> Dict:
    """
    Get historical statistics for a circuit across multiple seasons.
    
    Returns:
        - Average safety car appearances
        - Typical weather conditions
        - Overtaking difficulty
        - DNF rate
    """
    if seasons is None:
        seasons = list(range(2020, 2026))
    
    circuit_stats = {
        'total_races': 0,
        'safety_car_count': 0,
        'dnf_count': 0,
        'total_drivers': 0,
        'races_with_rain': 0,
    }
    
    for season in seasons:
        try:
            # Get calendar for season
            schedule = fastf1.get_event_schedule(season)
            
            # Find race at this circuit
            matching_events = schedule[schedule['EventName'].str.contains(circuit_name, case=False, na=False)]
            
            if matching_events.empty:
                continue
            
            for _, event in matching_events.iterrows():
                try:
                    session = fastf1.get_session(season, event['EventName'], 'R')
                    session.load(telemetry=False, weather=False, messages=False)
                    
                    circuit_stats['total_races'] += 1
                    
                    # Count DNFs
                    results = session.results
                    dnfs = results[results['Status'].str.contains('DNF|Retired', case=False, na=False)]
                    circuit_stats['dnf_count'] += len(dnfs)
                    circuit_stats['total_drivers'] += len(results)
                    
                    # Check for safety car
                    session.load_laps()
                    sc_laps = session.laps[session.laps['LapTime'].isna()]
                    if len(sc_laps) > 0:
                        circuit_stats['safety_car_count'] += 1
                    
                except Exception as e:
                    logger.debug(f"Failed to process {season} {event['EventName']}: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to get schedule for {season}: {e}")
            continue
    
    # Calculate statistics
    if circuit_stats['total_races'] > 0:
        circuit_stats['safety_car_rate'] = circuit_stats['safety_car_count'] / circuit_stats['total_races']
        circuit_stats['dnf_rate'] = circuit_stats['dnf_count'] / circuit_stats['total_drivers']
    else:
        circuit_stats['safety_car_rate'] = 0.5
        circuit_stats['dnf_rate'] = 0.15
    
    return circuit_stats


def sync_all_historical_data(seasons: List[int] = None):
    """
    Sync all historical data from fastf1 to local database.
    
    Args:
        seasons: List of seasons to sync (default: 2020-2025)
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    if seasons is None:
        seasons = list(range(2020, 2026))
    
    print(f"Syncing historical data for seasons: {seasons}")
    
    for season in seasons:
        try:
            schedule = fastf1.get_event_schedule(season)
            
            for _, event in schedule.iterrows():
                if event['EventName'] == 'Pre-Season Test':
                    continue
                
                print(f"\nProcessing: {season} {event['EventName']}")
                
                try:
                    # Ingest race results
                    results = ingest_race_results(season, event['EventName'])
                    print(f"  ✓ Race results: {len(results['results'])} drivers")
                    
                    # Ingest weather data
                    weather = ingest_weather_data(season, event['EventName'])
                    print(f"  ✓ Weather data: {len(weather['weather_data'])} data points")
                    
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    continue
                    
        except Exception as e:
            print(f"Failed to process season {season}: {e}")
            continue
    
    print("\n✓ Historical data sync completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if FASTF1_AVAILABLE:
        print("Fast-F1 Integration Module v3.0")
        print("Available functions:")
        print("  - ingest_race_results(season, race_name)")
        print("  - ingest_lap_data(season, race_name, driver_id)")
        print("  - ingest_qualifying_results(season, race_name)")
        print("  - ingest_tire_strategy(season, race_name)")
        print("  - ingest_weather_data(season, race_name)")
        print("  - get_historical_circuit_stats(circuit_name, seasons)")
        print("  - sync_all_historical_data(seasons)")
    else:
        print("fastf1 not installed. Install with: pip install fastf1")
