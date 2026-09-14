"""
Jolpica API client for F1 data.
Provides standings, race results, and qualifying data.
"""
import datetime as dt
import time
import requests
from typing import Optional, Dict, List, Any

from backend.app.data.api_client import APIClient
from backend.app.config.api_settings import api_settings
from backend.app.config.settings import settings


class JolpicaClient(APIClient):
    """Client for Jolpica F1 API."""
    
    def __init__(self):
        if not api_settings.is_enabled('jolpica'):
            raise ValueError("Jolpica API is not enabled in settings")
        super().__init__(api_settings.JOLPICA_BASE_URL)
    
    def get_driver_standings(self, season_year: int) -> Dict[str, Any]:
        """
        Get driver championship standings for a season.
        
        Returns:
            Dictionary with 'data', 'source', and 'provenance' keys
        """
        try:
            response = self.get(
                f'/f1/{season_year}/driverStandings.json',
                timeout=api_settings.LONG_TIMEOUT,
                cache_ttl=api_settings.CACHE_TTL_LONG
            )
            
            # If request failed, use fallback
            if response['source'] == 'error':
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_standings_fallback()
                return {
                    'data': fallback_data,
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated standings'
                    }
                }
            
            return response
        except Exception as e:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_standings_fallback()
            return {
                'data': fallback_data,
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated standings'
                }
            }
    
    def get_constructor_standings(self, season: int = None) -> Dict[str, Any]:
        """
        Get constructor championship standings for a season.
        
        Args:
            season: Season year (defaults to settings.SEASON_YEAR)
        
        Returns:
            Dictionary with standings data and source info
        """
        season = season or settings.SEASON_YEAR
        endpoint = api_settings.get_endpoint('jolpica', 'constructor_standings', season=season)
        
        if not endpoint:
            return self._error_response("Constructor standings endpoint not configured")
        
        response = self.get(endpoint, cache_ttl=api_settings.CACHE_TTL_LONG)
        
        if response['source'] == 'error':
            return self._fallback_constructor_standings(season)
        
        return response
    
    def get_race_result(self, season: int, round_number: int) -> Dict[str, Any]:
        """
        Get race results for a specific round.
        
        Args:
            season: Season year
            round_number: Round number
        
        Returns:
            Dictionary with race results and source info
        """
        endpoint = api_settings.get_endpoint('jolpica', 'race_result', season=season, round=round_number)
        
        if not endpoint:
            return self._error_response("Race result endpoint not configured")
        
        response = self.get(endpoint, cache_ttl=api_settings.CACHE_TTL_LONG)
        
        if response['source'] == 'error':
            return self._fallback_race_result(season, round_number)
        
        return response
    
    def get_qualifying_result(self, season_year: int, round_number: int) -> Dict[str, Any]:
        """
        Get qualifying results for a specific race.
        
        Returns:
            Dictionary with 'data', 'source', and 'provenance' keys
        """
        try:
            response = self.get(
                f'/f1/{season_year}/{round_number}/qualifying.json',
                timeout=api_settings.LONG_TIMEOUT,
                cache_ttl=api_settings.CACHE_TTL_LONG
            )
            
            # If request failed, use fallback
            if response['source'] == 'error':
                from backend.app.data.fallback import FallbackStrategy
                fallback_data = FallbackStrategy.get_grid_fallback()
                return {
                    'data': fallback_data,
                    'source': 'fallback',
                    'provenance': {
                        'source': 'fallback',
                        'cache_status': 'fallback',
                        'timestamp': dt.datetime.now().isoformat(),
                        'note': 'Using simulated grid positions'
                    }
                }
            
            return response
        except Exception as e:
            from backend.app.data.fallback import FallbackStrategy
            fallback_data = FallbackStrategy.get_grid_fallback()
            return {
                'data': fallback_data,
                'source': 'fallback',
                'provenance': {
                    'source': 'fallback',
                    'cache_status': 'fallback',
                    'timestamp': dt.datetime.now().isoformat(),
                    'note': 'Using simulated grid positions'
                }
            }
    
    def get_race_schedule(self, season: int = None) -> Dict[str, Any]:
        """
        Get complete race schedule for a season.
        
        Args:
            season: Season year (defaults to settings.SEASON_YEAR)
        
        Returns:
            Dictionary with schedule data and source info
        """
        season = season or settings.SEASON_YEAR
        endpoint = api_settings.get_endpoint('jolpica', 'race_schedule', season=season)
        
        if not endpoint:
            return self._error_response("Race schedule endpoint not configured")
        
        response = self.get(endpoint, cache_ttl=api_settings.CACHE_TTL_LONG)
        
        if response['source'] == 'error':
            return self._fallback_race_schedule(season)
        
        return response
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            'data': None,
            'source': 'error',
            'error': message,
        }
    
    def _fallback_driver_standings(self, season: int) -> Dict[str, Any]:
        """Fallback to simulated data when API fails."""
        # Import here to avoid circular dependency
        from backend.app.data.season_2026 import get_driver_standings
        
        if season == settings.SEASON_YEAR:
            return {
                'data': get_driver_standings(),
                'source': 'simulated',
                'note': 'Using season snapshot data',
            }
        
        return {
            'data': None,
            'source': 'simulated',
            'note': f'No simulated data available for season {season}',
        }
    
    def _fallback_constructor_standings(self, season: int) -> Dict[str, Any]:
        """Fallback to simulated data when API fails."""
        from backend.app.data.season_2026 import get_constructor_standings
        
        if season == settings.SEASON_YEAR:
            return {
                'data': get_constructor_standings(),
                'source': 'simulated',
                'note': 'Using season snapshot data',
            }
        
        return {
            'data': None,
            'source': 'simulated',
            'note': f'No simulated data available for season {season}',
        }
    
    def _fallback_race_result(self, season: int, round_number: int) -> Dict[str, Any]:
        """Fallback to simulated data when API fails."""
        from backend.app.data.season_2026 import get_race_result
        
        if season == settings.SEASON_YEAR:
            result = get_race_result(round_number)
            if result:
                return {
                    'data': result,
                    'source': 'simulated',
                    'note': 'Using season snapshot data',
                }
        
        return {
            'data': None,
            'source': 'simulated',
            'note': f'No simulated data available for season {season} round {round_number}',
        }
    
    def _fallback_qualifying_result(self, season: int, round_number: int) -> Dict[str, Any]:
        """Fallback to simulated data when API fails."""
        # Generate simulated qualifying based on driver strengths
        from backend.app.config.team_driver_lineup_2026 import get_all_drivers
        
        drivers = get_all_drivers()
        simulated_grid = sorted(
            drivers,
            key=lambda d: d['strength'] + (hash(f"{season}-{round_number}-{d['code']}") % 20),
            reverse=True,
        )
        
        grid_positions = {
            driver['code']: i + 1
            for i, driver in enumerate(simulated_grid)
        }
        
        return {
            'data': {
                'season': season,
                'round': round_number,
                'grid': grid_positions,
            },
            'source': 'simulated',
            'note': 'Simulated qualifying based on driver strengths',
        }
    
    def _fallback_race_schedule(self, season: int) -> Dict[str, Any]:
        """Fallback to simulated data when API fails."""
        if season == settings.SEASON_YEAR:
            from backend.app.data.calendar_2026 import CALENDAR_2026
            return {
                'data': CALENDAR_2026,
                'source': 'simulated',
                'note': 'Using calendar configuration',
            }
        
        return {
            'data': None,
            'source': 'simulated',
            'note': f'No simulated data available for season {season}',
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        timeout: int = None,
        use_cache: bool = True,
        cache_ttl: int = None,
    ) -> Dict:
        """
        Make HTTP request with retry logic and caching.
        
        Returns:
            Response dictionary with 'data', 'source', and 'provenance' keys
        """
        url = self._build_url(endpoint)
        timeout = timeout or api_settings.DEFAULT_TIMEOUT
        
        # Try cache first for GET requests
        if method.upper() == 'GET' and use_cache:
            cache_key = self._get_cache_key(url, params)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return {
                    'data': cached_response,
                    'source': 'cached',
                    'provenance': {
                        'source': 'jolpica',
                        'cache_status': 'hit',
                        'timestamp': dt.datetime.now().isoformat()
                    }
                }
        
        # Make request with retry logic
        last_exception = None
        for attempt in range(api_settings.MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=timeout,
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Cache successful GET responses
                if method.upper() == 'GET' and use_cache:
                    self._cache_response(cache_key, response_data, cache_ttl)
                
                return {
                    'data': response_data,
                    'source': 'live',
                    'provenance': {
                        'source': 'jolpica',
                        'cache_status': 'miss',
                        'timestamp': dt.datetime.now().isoformat()
                    }
                }
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                if response.status_code not in api_settings.RETRY_STATUS_CODES:
                    raise
                
                # Don't retry client errors (4xx) except rate limit (429)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    raise
            
            except requests.exceptions.RequestException as e:
                last_exception = e
            
            # Exponential backoff
            if attempt < api_settings.MAX_RETRIES - 1:
                backoff_time = api_settings.RETRY_BACKOFF_FACTOR ** attempt
                time.sleep(backoff_time)
        
        # All retries failed
        return {
            'data': None,
            'source': 'error',
            'provenance': {
                'source': 'jolpica',
                'cache_status': 'error',
                'timestamp': dt.datetime.now().isoformat(),
                'error': str(last_exception)
            }
        }
