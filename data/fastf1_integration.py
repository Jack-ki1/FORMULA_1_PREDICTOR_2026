"""
Fast-F1 Integration — Real F1 Data Pipeline for v3.0.

Integrates fastf1 library for:
- Historical race results ingestion
- Lap-by-lap telemetry data
- Tire compound and pit stop data
- Sector time analysis
- Qualifying session data
- Real-time weather conditions
- Car telemetry (speed, RPM, throttle, brake, DRS)
- Track position data (X/Y/Z coordinates)
- Driver comparison utilities
- ML feature extraction
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import FastF1
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
    Ingest race results from race session.
    """
    session = get_session(season, race_name, 'R')
    
    return {
        'circuit': session.event['Location'],
        'date': session.event['EventDate'],
        'winner': session.results.iloc[0]['Abbreviation'] if len(session.results) > 0 else None,
        'results': session.results,
    }


def ingest_lap_data(season: int, race_name: str, driver_id: str) -> Dict:
    """
    Ingest lap data for a specific driver.
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        driver_id: Driver abbreviation (e.g., 'VER', 'HAM')
    
    Returns:
        Dictionary with lap data including:
        - lap number
        - sector times
        - lap time
        - compound
        - tire age
    """
    session = get_session(season, race_name, 'R')
    
    # Get laps for the driver
    driver_laps = session.laps.pick_driver(driver_id.upper())
    
    laps = []
    for _, lap in driver_laps.iterrows():
        laps.append({
            'lap': int(lap['LapNumber']),
            'sector1': lap['Sector1Time'].total_seconds() if lap['Sector1Time'] else None,
            'sector2': lap['Sector2Time'].total_seconds() if lap['Sector2Time'] else None,
            'sector3': lap['Sector3Time'].total_seconds() if lap['Sector3Time'] else None,
            'lap_time': lap['LapTime'].total_seconds() if lap['LapTime'] else None,
            'compound': lap['Compound'],
            'tire_age': int(lap['TyreLife']),
        })
    
    return {
        'driver': driver_id,
        'laps': laps,
    }


def ingest_qualifying_results(season: int, race_name: str) -> Dict:
    """
    Ingest qualifying results from qualifying session.
    """
    session = get_session(season, race_name, 'Q')
    
    return {
        'circuit': session.event['Location'],
        'date': session.event['EventDate'],
        'results': session.results,
    }


def ingest_tire_strategy(season: int, race_name: str) -> Dict:
    """
    Ingest tire strategy data from race session.
    """
    session = get_session(season, race_name, 'R')
    
    # Get tire strategy data
    tire_strategy = []
    for driver in session.results['Abbreviation'].unique():
        driver_laps = session.laps.pick_driver(driver)
        stints = driver_laps['Compound'].value_counts().to_dict()
        tire_strategy.append({
            'driver': driver,
            'stints': stints,
        })
    
    return {
        'circuit': session.event['Location'],
        'tire_strategy': tire_strategy,
    }


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


def ingest_telemetry_data(season: int, race_name: str, driver_id: str) -> Dict:
    """
    Ingest car telemetry data for a specific driver.
    
    NEW FUNCTION: Provides access to car telemetry including:
    - Speed, RPM, throttle, brake
    - DRS status
    - Gear selection
    - X/Y track position
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        driver_id: Driver abbreviation (e.g., 'VER', 'HAM')
    
    Returns:
        Dictionary with telemetry data including:
        - car_data: Speed, RPM, throttle, brake, DRS, gear
        - pos_data: X/Y track coordinates
        - lap_info: Lap number, compound, tire age
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required. Install: pip install fastf1")
    
    session = get_session(season, race_name, 'R')
    
    # Get fastest lap for the driver
    try:
        driver_laps = session.laps.pick_driver(driver_id.upper())
        fastest_lap = driver_laps.pick_fastest()
        
        # Get car telemetry data
        car_data = fastest_lap.get_car_data()
        telemetry = []
        for _, data_point in car_data.iterrows():
            telemetry.append({
                'speed': float(data_point['Speed']) if data_point['Speed'] is not None else None,
                'rpm': float(data_point['RPM']) if data_point['RPM'] is not None else None,
                'throttle': float(data_point['Throttle']) if data_point['Throttle'] is not None else None,
                'brake': bool(data_point['Brake']) if data_point['Brake'] is not None else None,
                'drs': int(data_point['DRS']) if data_point['DRS'] is not None else None,
                'gear': int(data_point['nGear']) if data_point['nGear'] is not None else None,
                'time': data_point['Time'],
            })
        
        # Get position data (X/Y coordinates)
        pos_data = fastest_lap.get_pos_data()
        positions = []
        for _, pos_point in pos_data.iterrows():
            positions.append({
                'x': float(pos_point['X']) if pos_point['X'] is not None else None,
                'y': float(pos_point['Y']) if pos_point['Y'] is not None else None,
                'z': float(pos_point['Z']) if pos_point['Z'] is not None else None,
                'time': pos_point['Time'],
            })
        
        return {
            'driver': driver_id,
            'lap_number': int(fastest_lap['LapNumber']),
            'lap_time': fastest_lap['LapTime'].total_seconds() if fastest_lap['LapTime'] else None,
            'compound': fastest_lap['Compound'],
            'tire_age': int(fastest_lap['TyreLife']),
            'telemetry_points': len(telemetry),
            'car_data': telemetry,
            'position_data': positions,
        }
        
    except Exception as e:
        logger.error(f"Failed to get telemetry for {driver_id}: {e}")
        raise


def compare_drivers_telemetry(season: int, race_name: str, driver1: str, driver2: str) -> Dict:
    """
    Compare telemetry data between two drivers on their fastest laps.
    
    NEW FUNCTION: Enables driver performance comparison using:
    - Speed traces
    - Braking points
    - Throttle application
    - Corner exits
    
    Args:
        season: Year
        race_name: Race name or round
        driver1: First driver abbreviation
        driver2: Second driver abbreviation
    
    Returns:
        Dictionary with comparison metrics including:
        - avg_speed, max_speed for each driver
        - braking_intensity, throttle_application
        - lap_time difference
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    session = get_session(season, race_name, 'R')
    
    try:
        # Get fastest laps for both drivers
        lap1 = session.laps.pick_driver(driver1.upper()).pick_fastest()
        lap2 = session.laps.pick_driver(driver2.upper()).pick_fastest()
        
        # Get telemetry
        tel1 = lap1.get_car_data()
        tel2 = lap2.get_car_data()
        
        # Calculate comparison metrics
        comparison = {
            'driver1': {
                'id': driver1,
                'lap_time': lap1['LapTime'].total_seconds() if lap1['LapTime'] else None,
                'avg_speed': float(tel1['Speed'].mean()) if tel1['Speed'].notna().any() else None,
                'max_speed': float(tel1['Speed'].max()) if tel1['Speed'].notna().any() else None,
                'avg_throttle': float(tel1['Throttle'].mean()) if tel1['Throttle'].notna().any() else None,
                'braking_events': int((tel1['Brake'] == True).sum()) if 'Brake' in tel1.columns else None,
            },
            'driver2': {
                'id': driver2,
                'lap_time': lap2['LapTime'].total_seconds() if lap2['LapTime'] else None,
                'avg_speed': float(tel2['Speed'].mean()) if tel2['Speed'].notna().any() else None,
                'max_speed': float(tel2['Speed'].max()) if tel2['Speed'].notna().any() else None,
                'avg_throttle': float(tel2['Throttle'].mean()) if tel2['Throttle'].notna().any() else None,
                'braking_events': int((tel2['Brake'] == True).sum()) if 'Brake' in tel2.columns else None,
            },
            'lap_time_diff': None,
        }
        
        # Calculate lap time difference
        if comparison['driver1']['lap_time'] and comparison['driver2']['lap_time']:
            comparison['lap_time_diff'] = comparison['driver1']['lap_time'] - comparison['driver2']['lap_time']
        
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to compare {driver1} vs {driver2}: {e}")
        raise


def load_entire_season(season: int, session_type: str = 'R') -> List[Dict]:
    """
    Load all race results for an entire season with error handling.
    
    NEW FUNCTION: Matches the "Load an Entire Season" example from FastF1 docs.
    
    Args:
        season: Year (e.g., 2025)
        session_type: Session type ('R' for race, 'Q' for qualifying)
    
    Returns:
        List of dictionaries, one per race, with:
        - round number
        - race name
        - winner
        - results dataframe (or error message)
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    season_data = []
    
    try:
        schedule = fastf1.get_event_schedule(season)
    except Exception as e:
        logger.error(f"Failed to get schedule for {season}: {e}")
        return season_data
    
    for idx, event in schedule.iterrows():
        # Skip non-race events
        if event['EventName'] == 'Pre-Season Test':
            continue
        
        try:
            session = fastf1.get_session(season, event['EventName'], session_type)
            session.load(telemetry=False, weather=False, messages=False)
            
            race_info = {
                'round': int(event['RoundNumber']),
                'race_name': event['EventName'],
                'circuit': event['Location'],
                'date': event['EventDate'],
                'winner': session.results.iloc[0]['Abbreviation'] if len(session.results) > 0 else None,
                'results_count': len(session.results),
                'results': session.results,
            }
            season_data.append(race_info)
            
            logger.info(f"✓ Loaded: Round {race_info['round']} - {race_info['race_name']}")
            
        except Exception as e:
            logger.warning(f"✗ Failed to load: {event['EventName']} - {e}")
            season_data.append({
                'round': int(event['RoundNumber']),
                'race_name': event['EventName'],
                'error': str(e),
            })
            continue
    
    logger.info(f"Loaded {len(season_data)} races for {season}")
    return season_data


def extract_ml_features(season: int, race_name: str) -> Dict:
    """
    Extract ML-ready features from FastF1 data for prediction models.
    
    NEW FUNCTION: Provides features for:
    - Race winner prediction
    - Qualifying prediction
    - Pit stop strategy optimization
    - Driver performance ratings
    - Tire degradation models
    
    Args:
        season: Year
        race_name: Race name or round
    
    Returns:
        Dictionary with ML-ready features:
        - driver_features: Per-driver metrics (consistency, pace, tire degradation)
        - race_features: Race-level metrics (safety car rate, weather, overtaking)
        - strategy_features: Pit stop and tire strategy patterns
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required")
    
    session = get_session(season, race_name, 'R')
    laps = session.laps
    results = session.results
    
    # Driver-level features
    driver_features = {}
    for driver in results['Abbreviation'].unique():
        driver_laps = laps.pick_driver(driver)
        
        if len(driver_laps) == 0:
            continue
        
        # Calculate consistency (std of lap times)
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        lap_times = valid_laps['LapTime'].apply(lambda x: x.total_seconds() if x else None)
        lap_times = lap_times.dropna()
        
        # Tire degradation analysis
        stint_laps = driver_laps[['Compound', 'TyreLife', 'LapTime']].dropna()
        
        driver_features[driver] = {
            'total_laps': len(driver_laps),
            'avg_lap_time': float(lap_times.mean()) if len(lap_times) > 0 else None,
            'lap_time_std': float(lap_times.std()) if len(lap_times) > 1 else None,  # Consistency
            'fastest_lap': float(lap_times.min()) if len(lap_times) > 0 else None,
            'avg_tire_age': float(driver_laps['TyreLife'].mean()) if driver_laps['TyreLife'].notna().any() else None,
            'pit_stops': int(driver_laps['PitOutTime'].notna().sum()),
            'dnf': driver not in results[results['Status'].str.contains('Finished', na=False)]['Abbreviation'].values,
        }
    
    # Race-level features
    total_drivers = len(results)
    finished_drivers = len(results[results['Status'].str.contains('Finished', na=False)])
    dnf_count = total_drivers - finished_drivers
    
    # Safety car detection (laps with no time)
    sc_laps = laps[laps['LapTime'].isna()]
    safety_car_appearances = len(sc_laps) > 0
    
    # Weather features
    weather_data = session.weather_data
    avg_air_temp = float(weather_data['AirTemp'].mean()) if weather_data['AirTemp'].notna().any() else None
    rained = bool(weather_data['Rainfall'].any()) if 'Rainfall' in weather_data.columns else False
    
    race_features = {
        'total_drivers': total_drivers,
        'finished_drivers': finished_drivers,
        'dnf_count': dnf_count,
        'dnf_rate': dnf_count / total_drivers if total_drivers > 0 else 0,
        'safety_car': safety_car_appearances,
        'avg_air_temp': avg_air_temp,
        'rained': rained,
        'total_laps': len(laps),
    }
    
    # Strategy features
    compound_usage = laps['Compound'].value_counts().to_dict() if laps['Compound'].notna().any() else {}
    avg_stint_length = float(laps.groupby('Driver')['TyreLife'].max().mean()) if laps['TyreLife'].notna().any() else None
    
    strategy_features = {
        'compound_usage': compound_usage,
        'avg_stint_length': avg_stint_length,
        'total_pit_stops': int(laps['PitOutTime'].notna().sum()),
    }
    
    return {
        'race_name': session.event['EventName'],
        'driver_features': driver_features,
        'race_features': race_features,
        'strategy_features': strategy_features,
    }

# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    "FASTF1_AVAILABLE",
    "get_session",
    "ingest_race_results",
    "ingest_lap_data",
    "ingest_qualifying_results",
    "ingest_tire_strategy",
    "ingest_weather_data",
    "ingest_telemetry_data",              # NEW
    "compare_drivers_telemetry",          # NEW
    "load_entire_season",                 # NEW
    "extract_ml_features",                # NEW
]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if FASTF1_AVAILABLE:
        print("Fast-F1 Integration Module v3.0 — ENHANCED")
        print("=" * 60)
        print("\nCore Functions:")
        print("  - get_session(season, race_name, session_type)")
        print("  - ingest_race_results(season, race_name)")
        print("  - ingest_lap_data(season, race_name, driver_id)")
        print("  - ingest_qualifying_results(season, race_name)")
        print("  - ingest_tire_strategy(season, race_name)")
        print("  - ingest_weather_data(season, race_name)")
        print("\nNEW Functions (v3.0 Enhanced):")
        print("  - ingest_telemetry_data(season, race_name, driver_id)")
        print("    → Speed, RPM, throttle, brake, DRS, gear, X/Y position")
        print("  - compare_drivers_telemetry(season, race_name, driver1, driver2)")
        print("    → Compare speed traces, braking, throttle application")
        print("  - load_entire_season(season, session_type)")
        print("    → Load all races with error handling")
        print("  - extract_ml_features(season, race_name)")
        print("    → ML-ready features: consistency, tire deg, race stats")
        print("\nUtility Functions:")
        print("  - get_historical_circuit_stats(circuit_name, seasons)")
        print("  - sync_all_historical_data(seasons)")
        print("\n" + "=" * 60)
        print("Install fastf1: pip install fastf1")
        print("Docs: https://docs.fastf1.dev")
    else:
        print("fastf1 not installed. Install with: pip install fastf1")
