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

import json
import fastf1
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Apply cache fix BEFORE importing fastf1 to avoid RequestsCookieJar NameError on Python 3.14
from data._fastf1_cache_fix import apply_fastf1_cache_fix, configure_fastf1_offline_mode  # noqa: E402, F401
apply_fastf1_cache_fix()
configure_fastf1_offline_mode()

# Try to import FastF1 - Suppress warning on import, only warn when actually used
FASTF1_AVAILABLE = None  # Use None to indicate not yet checked
SessionNotAvailableError = None  # Will be set to the correct exception if import succeeds

def _init_fastf1():
    """Initialize FastF1 library on demand."""
    global FASTF1_AVAILABLE, SessionNotAvailableError
    if FASTF1_AVAILABLE is not None:  # Already checked
        return FASTF1_AVAILABLE
    
    try:
        import fastf1
        from fastf1 import plotting
        from fastf1.exceptions import InvalidSessionError as SessionNotAvailableErrorException
        # Update the global variable to the actual exception class
        globals()['SessionNotAvailableError'] = SessionNotAvailableErrorException
        FASTF1_AVAILABLE = True
        plotting.setup_mpl()
        return True
    except ImportError:
        FASTF1_AVAILABLE = False
        return False


def is_fastf1_available():
    """Check if FastF1 library is available."""
    return _init_fastf1()


def get_fastf1_module():
    """Get the FastF1 module if available, raises ImportError if not."""
    if not _init_fastf1():
        raise ImportError("fastf1 library not installed. Install with: pip install fastf1")
    import fastf1
    return fastf1


def get_session(season: int, race_name: str, session_type: str = 'R',
                load_telemetry: bool = False, load_weather: bool = False, load_messages: bool = False):
    """
    Get F1 session data from fastf1.
    
    Args:
        season: Year (e.g., 2025)
        race_name: Race name or round number
        session_type: 'P1', 'P2', 'P3', 'Q', 'S', 'SQ', 'R'
        load_telemetry: Whether to load telemetry data
        load_weather: Whether to load weather data
        load_messages: Whether to load race control messages
    
    Returns:
        fastf1.core.Session object or None if data not available
    
    Raises:
        ImportError: If fastf1 is not installed
    """
    if not _init_fastf1():  # Initialize if needed
        raise ImportError("fastf1 library not installed. Install with: pip install fastf1")
    
    import fastf1  # Import here after verification
    try:
        session = fastf1.get_session(season, race_name, session_type)
        # Load with configurable data based on parameters
        session.load(telemetry=load_telemetry, weather=load_weather, messages=load_messages)
        return session
    except Exception as e:
        # Check if this is a "session not available" error (future race)
        if SessionNotAvailableError and isinstance(e, SessionNotAvailableError):
            logger.info(f"Future race data not available yet: {season} {race_name} {session_type}")
            return None
        
        error_msg = str(e).lower()
        if 'no data for this session' in error_msg:
            logger.info(f"Future race data not available yet: {season} {race_name} {session_type}")
            return None

        logger.warning(f"Failed to load session {season} {race_name} {session_type}: {e}")
        # For truly future races (beyond current year), return None
        current_year = datetime.now().year
        if season > current_year:
            logger.info(f"Future race data not available yet: {season} {race_name}")
            return None
        # For current/past years, re-raise the exception to allow proper error handling
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
    if not _init_fastf1():  # Initialize if needed
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
    if not _init_fastf1():  # Initialize if needed
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
    
    # For future seasons (2026+), return empty list since data doesn't exist yet
    current_year = datetime.now().year
    if season > current_year:
        logger.info(f"Season {season} is in the future — no FastF1 data available yet.")
        return []
    
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
            # Log connection errors at debug level to reduce noise for future seasons
            error_str = str(e).lower()
            if 'connection' in error_str or 'dns' in error_str or 'getaddrinfo' in error_str:
                logger.debug(f"✗ Connection error for {event['EventName']} (expected for future/partial seasons): {e}")
            else:
                logger.warning(f"✗ Failed to load: {event['EventName']} - {e}")
            
            season_data.append({
                'round': int(event['RoundNumber']),
                'race_name': event['EventName'],
                'error': str(e),
            })
            continue
    
    logger.info(f"Loaded {len(season_data)} races for {season}")
    return season_data


def extract_sector_performance_features(season: int, race_name: str) -> Dict:
    """
    Extract sector-level performance features from FastF1 data.
    
    Provides per-driver 'which type of corner/straight are they strongest at' profile
    by analyzing sector times normalized against the field.
    
    Args:
        season: Year
        race_name: Race name or round
    
    Returns:
        Dictionary with sector performance features:
        - driver_sector_features: Per-driver sector time analysis
        - circuit_sector_characteristics: Circuit-specific sector difficulty data
    """
    if not _init_fastf1():  # Use the new function
        raise ImportError("fastf1 library required")
    
    # Load session with telemetry data for sector analysis
    session = get_session(season, race_name, 'R', load_telemetry=True)
    laps = session.laps
    results = session.results
    
    # Driver-level sector features
    driver_sector_features = {}
    for driver in results['Abbreviation'].unique():
        driver_laps = laps.pick_driver(driver)
        
        if len(driver_laps) == 0:
            continue
        
        # Extract sector times for the driver
        sector_times = {
            'sector1': driver_laps['Sector1Time'].dropna(),
            'sector2': driver_laps['Sector2Time'].dropna(), 
            'sector3': driver_laps['Sector3Time'].dropna()
        }
        
        # Calculate average sector times and compare to field
        field_sector_averages = {
            'sector1': laps['Sector1Time'].mean(),
            'sector2': laps['Sector2Time'].mean(),
            'sector3': laps['Sector3Time'].mean()
        }
        
        driver_sector_averages = {
            'sector1': sector_times['sector1'].mean() if len(sector_times['sector1']) > 0 else None,
            'sector2': sector_times['sector2'].mean() if len(sector_times['sector2']) > 0 else None,
            'sector3': sector_times['sector3'].mean() if len(sector_times['sector3']) > 0 else None
        }
        
        # Calculate sector-specific performance (relative to field average)
        sector_performance = {}
        for sector in ['sector1', 'sector2', 'sector3']:
            if driver_sector_averages[sector] and field_sector_averages[sector]:
                # Negative = faster than field average (better performance)
                sector_performance[sector] = float(driver_sector_averages[sector] - field_sector_averages[sector])
            else:
                sector_performance[sector] = 0.0  # Neutral if no data
        
        driver_sector_features[driver] = {
            'sector_performance': sector_performance,
            'laps_analyzed': len(driver_laps),
            'avg_sector1_time': float(driver_sector_averages['sector1']) if driver_sector_averages['sector1'] else None,
            'avg_sector2_time': float(driver_sector_averages['sector2']) if driver_sector_averages['sector2'] else None,
            'avg_sector3_time': float(driver_sector_averages['sector3']) if driver_sector_averages['sector3'] else None,
        }
    
    # Circuit-level sector characteristics
    circuit_sector_characteristics = {
        'field_avg_sector1': float(field_sector_averages['sector1']) if field_sector_averages['sector1'] else None,
        'field_avg_sector2': float(field_sector_averages['sector2']) if field_sector_averages['sector2'] else None,
        'field_avg_sector3': float(field_sector_averages['sector3']) if field_sector_averages['sector3'] else None,
    }
    
    return {
        'driver_sector_features': driver_sector_features,
        'circuit_sector_characteristics': circuit_sector_characteristics
    }


def extract_braking_aggression_features(season: int, race_name: str) -> Dict:
    """
    Extract braking/throttle aggression metrics from telemetry data.
    
    Provides 'late-braking frequency' and 'throttle application variance' metrics
    that correlate with overtaking aggression and incident risk.
    
    Args:
        season: Year
        race_name: Race name or round
    
    Returns:
        Dictionary with braking aggression features:
        - driver_aggression_metrics: Per-driver aggression indicators
    """
    if not _init_fastf1():  # Use the new function
        raise ImportError("fastf1 library required")
    
    # Load session with telemetry data for braking analysis
    session = get_session(season, race_name, 'R', load_telemetry=True)
    
    # This would normally access telemetry data to analyze braking patterns
    # Since we don't have the actual telemetry processing functions implemented yet,
    # we'll return a placeholder structure
    driver_aggression_metrics = {}
    
    # Note: Actual implementation would use session.laps.pick_driver(abbr).get_telemetry()
    # to get speed/brake/throttle data and calculate late-braking frequency
    
    return {
        'driver_aggression_metrics': driver_aggression_metrics,
        'analysis_available': False  # Indicates this feature isn't fully implemented yet
    }


def extract_drs_effectiveness_features(season: int, race_name: str) -> Dict:
    """
    Extract DRS zone effectiveness per circuit from telemetry data.
    
    Args:
        season: Year
        race_name: Race name or round
    
    Returns:
        Dictionary with DRS effectiveness features:
        - drs_zone_analysis: DRS usage and effectiveness data per zone
    """
    if not _init_fastf1():  # Use the new function
        raise ImportError("fastf1 library required")
    
    # Load session with telemetry data for DRS analysis
    session = get_session(season, race_name, 'R', load_telemetry=True)
    
    # Placeholder for DRS analysis
    drs_zone_analysis = {}
    
    return {
        'drs_zone_analysis': drs_zone_analysis,
        'analysis_available': False  # Indicates this feature isn't fully implemented yet
    }


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
    if not _init_fastf1():  # Use the new function
        raise ImportError("fastf1 library required")
    
    # Load session with weather data to make weather features available
    session = get_session(season, race_name, 'R', load_weather=True)
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

def _serialize_value(value: Any) -> Any:
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if isinstance(value, (datetime,)):
        return value.isoformat()
    try:
        return value.item()
    except Exception:
        return str(value)


def _dataframe_to_records(df):
    records = []
    for _, row in df.iterrows():
        record = {k: _serialize_value(v) for k, v in row.items()}
        records.append(record)
    return records


def sync_all_historical_data(seasons: List[int], output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Sync historical FastF1 data for the given seasons and persist structured JSON.

    Args:
        seasons: List of years to sync.
        output_dir: Optional directory path to save JSON exports.

    Returns:
        Summary dictionary with synced seasons, files, and errors.
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required. Install with: pip install fastf1")

    output_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "historical")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "seasons_synced": 0,
        "files": [],
        "errors": [],
    }

    current_year = datetime.now().year

    for season in seasons:
        # Skip future seasons — no FastF1 data available yet
        if season > current_year:
            logger.info(f"Skipping future season {season} — no FastF1 data available.")
            continue

        try:
            season_data = []
            schedule = fastf1.get_event_schedule(season)
            for _, event in schedule.iterrows():
                if 'Test' in event['EventName']:
                    continue

                race_info = {
                    'round': int(event['RoundNumber']),
                    'race_name': event['EventName'],
                    'circuit': event['Location'],
                    'date': str(event['EventDate']),
                    'results': [],
                    'winner': None,
                    'error': None,
                }

                try:
                    session = fastf1.get_session(season, event['EventName'], 'R')
                    session.load(telemetry=False, weather=False, messages=False)
                    race_info['winner'] = session.results.iloc[0]['Abbreviation'] if len(session.results) > 0 else None
                    race_info['results'] = _dataframe_to_records(session.results)
                except Exception as inner_err:
                    error_str = str(inner_err).lower()
                    if 'connection' in error_str or 'dns' in error_str or 'getaddrinfo' in error_str:
                        logger.debug(f"Connection error for {event['EventName']} (expected): {inner_err}")
                    else:
                        logger.warning(f"Failed to load {event['EventName']}: {inner_err}")
                    race_info['error'] = str(inner_err)

                season_data.append(race_info)

            path = output_dir / f"fastf1_season_{season}.json"
            with path.open('w', encoding='utf-8') as f:
                json.dump(season_data, f, indent=2)

            summary['seasons_synced'] += 1
            summary['files'].append(str(path))
        except Exception as err:
            summary['errors'].append(f"{season}: {err}")

    return summary


def get_historical_circuit_stats(season: int, circuit_name: str) -> Dict[str, Any]:
    """
    Return basic historical stats for a single circuit from FastF1.

    Args:
        season: Year to inspect.
        circuit_name: Circuit or event name.

    Returns:
        Dictionary with summary stats for the circuit.
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("fastf1 library required. Install with: pip install fastf1")

    schedule = fastf1.get_event_schedule(season)
    circuit_rows = schedule[schedule['EventName'].str.contains(circuit_name, case=False, na=False)]
    if circuit_rows.empty:
        raise ValueError(f"Circuit not found in FastF1 schedule: {circuit_name}")

    stats = {
        'season': season,
        'event': circuit_rows.iloc[0]['EventName'],
        'location': circuit_rows.iloc[0]['Location'],
        'round': int(circuit_rows.iloc[0]['RoundNumber']),
    }
    return stats


# ── OpenF1 Supplement Functions ────────────────────────────────────────────────
# These functions supplement FastF1 data with live data from the OpenF1 API.
# They provide real-time weather, race control events, and telemetry cross-validation.

def get_openf1_weather_supplement(year: int, meeting_name: str) -> Dict[str, Any]:
    """
    Get weather data from OpenF1 for a race weekend.
    
    Supplements FastF1 weather data with OpenF1's more granular
    track temperature, humidity, wind, and rain data.
    
    Args:
        year: Season year
        meeting_name: Meeting name (e.g., "Monaco")
    
    Returns:
        Dict with weather summary from OpenF1, or empty dict if unavailable
    """
    try:
        from data.openf1_client import get_openf1_client
        client = get_openf1_client()
        return client.get_weather_summary_for_meeting(year, meeting_name)
    except Exception as e:
        logger.debug(f"OpenF1 weather supplement failed: {e}")
        return {}


def get_openf1_safety_car_data(year: int, meeting_name: str) -> Dict[str, Any]:
    """
    Get safety car and race control data from OpenF1.
    
    Provides more detailed safety car deployment info than FastF1,
    including VSC periods, red flags, and penalty data.
    
    Args:
        year: Season year
        meeting_name: Meeting name
    
    Returns:
        Dict with safety car summary, or empty dict if unavailable
    """
    try:
        from data.openf1_client import get_openf1_client
        client = get_openf1_client()
        return client.get_safety_car_summary_for_meeting(year, meeting_name)
    except Exception as e:
        logger.debug(f"OpenF1 safety car supplement failed: {e}")
        return {}


def get_combined_weather_forecast(year: int, meeting_name: str) -> Dict[str, Any]:
    """
    Combine weather data from FastF1 (historical) and OpenF1 (live).
    
    Uses FastF1 for historical weather patterns and OpenF1 for
    current conditions. Provides a unified weather profile for
    prediction models.
    
    Args:
        year: Season year
        meeting_name: Meeting name
    
    Returns:
        Dict with combined weather data from both sources
    """
    combined = {
        "source": "combined",
        "fastf1": {},
        "openf1": {},
    }
    
    # Get FastF1 weather (historical patterns)
    try:
        session = get_session(year, meeting_name, "Race")
        if session:
            session.load(telemetry=False, weather=True, messages=False)
            if hasattr(session, 'weather_data') and session.weather_data is not None:
                wd = session.weather_data
                combined["fastf1"] = {
                    "avg_air_temp": float(wd['AirTemp'].mean()) if 'AirTemp' in wd.columns else None,
                    "avg_track_temp": float(wd['TrackTemp'].mean()) if 'TrackTemp' in wd.columns else None,
                    "rained": bool(wd['Rainfall'].any()) if 'Rainfall' in wd.columns else False,
                    "humidity": float(wd['Humidity'].mean()) if 'Humidity' in wd.columns else None,
                    "wind_speed": float(wd['WindSpeed'].mean()) if 'WindSpeed' in wd.columns else None,
                }
    except Exception as e:
        logger.debug(f"FastF1 weather failed: {e}")
    
    # Get OpenF1 weather (live/current)
    try:
        openf1_weather = get_openf1_weather_supplement(year, meeting_name)
        if openf1_weather:
            combined["openf1"] = openf1_weather
    except Exception as e:
        logger.debug(f"OpenF1 weather failed: {e}")
    
    # Merge: prefer OpenF1 for live data, FastF1 for historical
    merged = {}
    for key in ["avg_air_temp", "avg_track_temp", "rained", "humidity", "wind_speed"]:
        openf1_val = combined["openf1"].get(key)
        fastf1_val = combined["fastf1"].get(key)
        merged[key] = openf1_val if openf1_val is not None else fastf1_val
    
    merged["sources"] = {
        "fastf1": bool(combined["fastf1"]),
        "openf1": bool(combined["openf1"]),
    }
    
    return merged


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = [
    'FASTF1_AVAILABLE',
    'is_fastf1_available',
    'get_session',
    'ingest_race_results',
    'ingest_lap_data',
    'ingest_qualifying_results',
    'ingest_tire_strategy',
    'ingest_weather_data',
    'ingest_telemetry_data',
    'compare_drivers_telemetry',
    'load_entire_season',
    'extract_ml_features',
    'get_historical_circuit_stats',
    'sync_all_historical_data',
    'get_openf1_weather_supplement',
    'get_openf1_safety_car_data',
    'get_combined_weather_forecast',
    'extract_sector_performance_features',  # NEW: Sector analysis
    'extract_braking_aggression_features',  # NEW: Braking analysis
    'extract_drs_effectiveness_features',   # NEW: DRS analysis
]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if is_fastf1_available():  # Use the function instead of direct variable
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


# Export public functions
__all__ = [
    'FASTF1_AVAILABLE',
    'is_fastf1_available',
    'get_session',
    'ingest_race_results',
    'ingest_lap_data',
    'ingest_qualifying_results',
    'ingest_tire_strategy',
    'ingest_weather_data',
    'ingest_telemetry_data',
    'compare_drivers_telemetry',
    'load_entire_season',
    'extract_ml_features',
    'get_historical_circuit_stats',
    'sync_all_historical_data',
    'get_openf1_weather_supplement',
    'get_openf1_safety_car_data',
    'get_combined_weather_forecast',
    'extract_sector_performance_features',  # NEW: Sector analysis
    'extract_braking_aggression_features',  # NEW: Braking analysis
    'extract_drs_effectiveness_features',   # NEW: DRS analysis
]
