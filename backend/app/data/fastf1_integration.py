"""
FastF1 integration for lap-by-lap telemetry and practice/qualifying data.
This provides detailed telemetry data for advanced analysis.
"""
import fastf1
from typing import Optional, Dict, Any
import datetime as dt
from backend.app.config.api_settings import api_settings
from backend.app.config.settings import settings


class FastF1Integration:
    """Integration with FastF1 for detailed telemetry data."""
    
    def __init__(self):
        if not api_settings.is_enabled('fastf1'):
            raise ValueError("FastF1 integration is not enabled in settings")
        
        # Configure FastF1 cache
        if settings.FASTF1_CACHE_ENABLED:
            fastf1.Cache.enable_cache(settings.FASTF1_CACHE_PATH)
        else:
            fastf1.Cache.disable_cache()
    
    def get_session(self, year: int, round_number: int, session_type: str) -> Optional[fastf1.core.Session]:
        """
        Get a FastF1 session object.
        
        Returns:
            FastF1 Session object or None if unavailable
        """
        try:
            session = fastf1.get_session(year, round_number, session_type)
            session.load()
            return {
                'data': session,
                'source': 'live',
                'provenance': {
                    'source': 'fastf1',
                    'cache_status': 'miss',
                    'timestamp': dt.datetime.now().isoformat()
                }
            }
        except Exception as e:
            print(f"FastF1 error loading session: {e}")
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_weather_fallback()
            return {
                'data': fallback_data,
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated weather data'
                }
            }
    
    def get_lap_times(self, year: int, round_number: int, session_type: str) -> Dict[str, Any]:
        """
        Get lap times for a session.
        
        Returns:
            Dictionary with lap times data and provenance info
        """
        try:
            session_result = self.get_session(year, round_number, session_type)
            if not session_result or not session_result['data']:
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_lap_times_fallback()
                return {
                    'data': fallback_data['lap_times'],
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated lap times'
                    }
                }
            
            session = session_result['data']
            
            lap_data = []
            for driver in session.drivers:
                driver_laps = session.laps[session.laps['DriverNumber'] == driver]
                for _, lap in driver_laps.iterrows():
                    lap_data.append({
                        'driver': driver,
                        'lap_number': lap['LapNumber'],
                        'lap_time': str(lap['LapTime']) if lap['LapTime'] else None,
                        'sector_times': [
                            str(lap['Sector1Time']) if lap['Sector1Time'] else None,
                            str(lap['Sector2Time']) if lap['Sector2Time'] else None,
                            str(lap['Sector3Time']) if lap['Sector3Time'] else None,
                        ],
                        'compound': lap['Compound'],
                        'tyre_life': lap['TyreLife'],
                        'fresh_tyre': lap['FreshTyre'],
                    })
            
            return {
                'data': lap_data,
                'source': 'live',
                'provenance': {
                    'source': 'fastf1',
                    'cache_status': 'miss',
                    'timestamp': dt.datetime.now().isoformat()
                }
            }
            
        except Exception:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_lap_times_fallback()
            return {
                'data': fallback_data['lap_times'],
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated lap times'
                }
            }
    
    def get_telemetry(self, year: int, round_number: int, session_type: str, driver: str) -> Dict[str, Any]:
        """
        Get detailed telemetry for a specific driver.
        
        Returns:
            Dictionary with telemetry data and provenance info
        """
        try:
            session_result = self.get_session(year, round_number, session_type)
            if not session_result or not session_result['data']:
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_weather_fallback()
                return {
                    'data': fallback_data['weather'],
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated weather data'
                    }
                }
            
            session = session_result['data']
            
            driver_laps = session.laps[session.laps['Driver'] == driver]
            if driver_laps.empty:
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_weather_fallback()
                return {
                    'data': fallback_data['weather'],
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated weather data'
                    }
                }
            
            # Get telemetry for fastest lap
            fastest_lap = driver_laps.loc[driver_laps['LapTime'].idxmin()]
            telemetry = fastest_lap.get_telemetry()
            
            telemetry_data = {
                'driver': driver,
                'lap_number': fastest_lap['LapNumber'],
                'speed': telemetry['Speed'].tolist(),
                'throttle': telemetry['Throttle'].tolist(),
                'brake': telemetry['Brake'].tolist(),
                'gear': telemetry['nGear'].tolist(),
                'rpm': telemetry['RPM'].tolist(),
                'distance': telemetry['Distance'].tolist(),
            }
            
            return {
                'data': telemetry_data,
                'source': 'live',
                'provenance': {
                    'source': 'fastf1',
                    'cache_status': 'miss',
                    'timestamp': dt.datetime.now().isoformat()
                }
            }
            
        except Exception:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_weather_fallback()
            return {
                'data': fallback_data['weather'],
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated weather data'
                }
            }
    
    def get_weather_data(self, year: int, round_number: int, session_type: str) -> Dict[str, Any]:
        """
        Get weather data for a session.
        
        Returns:
            Dictionary with weather data and provenance info
        """
        try:
            session_result = self.get_session(year, round_number, session_type)
            if not session_result or not session_result['data']:
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_weather_fallback()
                return {
                    'data': fallback_data['weather'],
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated weather data'
                    }
                }
            
            session = session_result['data']
            weather_data = session.weather_data
            
            weather_list = []
            for _, row in weather_data.iterrows():
                weather_list.append({
                    'time': str(row['Time']),
                    'air_temp': row['AirTemp'],
                    'track_temp': row['TrackTemp'],
                    'humidity': row['Humidity'],
                    'pressure': row['Pressure'],
                    'wind_speed': row['WindSpeed'],
                    'wind_direction': row['WindDirection'],
                    'rain': row['Rainfall'],
                })
            
            return {
                'data': weather_list,
                'source': 'live',
                'provenance': {
                    'source': 'fastf1',
                    'cache_status': 'miss',
                    'timestamp': dt.datetime.now().isoformat()
                }
            }
            
        except Exception:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_weather_fallback()
            return {
                'data': fallback_data['weather'],
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated weather data'
                }
            }
    
    def get_session_results(self, year: int, round_number: int, session_type: str) -> Dict[str, Any]:
        """
        Get session results (practice/qualifying/race).
        
        Returns:
            Dictionary with results data and provenance info
        """
        try:
            session_result = self.get_session(year, round_number, session_type)
            if not session_result or not session_result['data']:
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_standings_fallback()
                return {
                    'data': fallback_data['driver_standings'],
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated standings'
                    }
                }
            
            session = session_result['data']
            results = session.results
            
            results_list = []
            for _, result in results.iterrows():
                results_list.append({
                    'position': result['Position'],
                    'driver': result['DriverNumber'],
                    'driver_name': result['Abbreviation'],
                    'team': result['TeamName'],
                    'lap_time': str(result['Time']) if result['Time'] else None,
                    'gap': str(result['Delta']) if result['Delta'] else None,
                    'laps': result['Laps'],
                    'status': result['Status'],
                })
            
            return {
                'data': results_list,
                'source': 'live',
                'provenance': {
                    'source': 'fastf1',
                    'cache_status': 'miss',
                    'timestamp': dt.datetime.now().isoformat()
                }
            }
            
        except Exception:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_standings_fallback()
            return {
                'data': fallback_data['driver_standings'],
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated standings'
                }
            }