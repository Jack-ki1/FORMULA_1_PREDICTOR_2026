"""
OpenF1 API client for live session and telemetry data.
This is a new integration for real-time live timing data.
"""
import datetime as dt
import time
import requests
from typing import Optional, Dict, Any

from backend.app.data.api_client import APIClient
from backend.app.config.api_settings import api_settings


class OpenF1Client(APIClient):
    """Client for OpenF1 API (live session and telemetry data)."""
    
    def __init__(self):
        if not api_settings.is_enabled('openf1'):
            raise ValueError("OpenF1 API is not enabled in settings")
        super().__init__(api_settings.OPENF1_BASE_URL)
    
    def get_sessions(self, season_year: int) -> Dict[str, Any]:
        """
        Get sessions for a season.
        
        Returns:
            Dictionary with 'data', 'source', and 'provenance' keys
        """
        try:
            response = self.get(
                '/v1/sessions',
                timeout=30,
                cache_ttl=60
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
        except Exception:
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
    
    def get_session_key(self, meeting_key: int, session_name: str) -> Optional[int]:
        """
        Get session key for a specific meeting and session type.
        
        Args:
            meeting_key: Meeting identifier
            session_name: Session name (e.g., 'Qualifying', 'Race')
        
        Returns:
            Session key if found, None otherwise
        """
        response = self.get_sessions(year=None, meeting_key=meeting_key)
        
        if response['source'] == 'error' or not response['data']:
            return None
        
        sessions = response['data']
        for session in sessions:
            if session.get('session_name') == session_name:
                return session.get('session_key')
        
        return None
    
    def get_drivers(self, session_key: int) -> Dict[str, Any]:
        """
        Get drivers for a session.
        
        Returns:
            Dictionary with 'data', 'source', and 'provenance' keys
        """
        try:
            response = self.get(
                f'/v1/drivers?session_key={session_key}',
                timeout=self.settings.LONG_TIMEOUT,
                cache_ttl=self.api_settings.CACHE_TTL_LONG
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
        except Exception:
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
    
    def get_live_positions(self, session_key: int) -> Dict[str, Any]:
        """
        Get live position data for a session.
        
        Args:
            session_key: Session identifier
        
        Returns:
            Dictionary with position data and source info
        """
        params = {'session_key': session_key}
        endpoint = api_settings.get_endpoint('openf1', 'position')
        
        if not endpoint:
            return self._error_response("Position endpoint not configured")
        
        # Don't cache live position data
        response = self.get(endpoint, params=params, use_cache=False)
        
        if response['source'] == 'error':
            return self._fallback_positions(session_key)
        
        return response
    
    def get_car_data(self, session_key: int, driver_number: int) -> Dict[str, Any]:
        """
        Get car telemetry data for a specific driver.
        
        Args:
            session_key: Session identifier
            driver_number: Driver number
        
        Returns:
            Dictionary with car data and source info
        """
        params = {
            'session_key': session_key,
            'driver_number': driver_number,
        }
        endpoint = api_settings.get_endpoint('openf1', 'car_data')
        
        if not endpoint:
            return self._error_response("Car data endpoint not configured")
        
        response = self.get(endpoint, params=params, cache_ttl=api_settings.CACHE_TTL_SHORT)
        
        if response['source'] == 'error':
            return self._fallback_car_data(session_key, driver_number)
        
        return response
    
    def get_team_radio(self, session_key: int, driver_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Get team radio messages for a session.
        
        Args:
            session_key: Session identifier
            driver_number: Optional specific driver number
        
        Returns:
            Dictionary with radio data and source info
        """
        params = {'session_key': session_key}
        if driver_number:
            params['driver_number'] = driver_number
        
        endpoint = api_settings.get_endpoint('openf1', 'team_radio')
        
        if not endpoint:
            return self._error_response("Team radio endpoint not configured")
        
        response = self.get(endpoint, params=params, cache_ttl=api_settings.CACHE_TTL_SHORT)
        
        if response['source'] == 'error':
            return self._fallback_team_radio(session_key)
        
        return response
    
    def get_race_control(self, session_key: int) -> Dict[str, Any]:
        """
        Get race control messages for a session.
        
        Args:
            session_key: Session identifier
        
        Returns:
            Dictionary with race control data and source info
        """
        params = {'session_key': session_key}
        endpoint = api_settings.get_endpoint('openf1', 'race_control')
        
        if not endpoint:
            return self._error_response("Race control endpoint not configured")
        
        # Don't cache race control messages
        response = self.get(endpoint, params=params, use_cache=False)
        
        if response['source'] == 'error':
            return self._fallback_race_control(session_key)
        
        return response
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            'data': None,
            'source': 'error',
            'error': message,
        }
    
    def _fallback_sessions(self, year: int) -> Dict[str, Any]:
        """Fallback when API fails."""
        return {
            'data': [],
            'source': 'simulated',
            'note': f'OpenF1 API unavailable - no session data for {year}',
        }
    
    def _fallback_drivers(self, session_key: int) -> Dict[str, Any]:
        """Fallback when API fails."""
        from backend.app.config.team_driver_lineup_2026 import get_all_drivers
        
        drivers = get_all_drivers()
        return {
            'data': [
                {
                    'driver_number': d['number'],
                    'name_acronym': d['code'],
                    'team_name': d['team_name'],
                }
                for d in drivers
            ],
            'source': 'simulated',
            'note': 'Using static driver roster',
        }
    
    def _fallback_positions(self, session_key: int) -> Dict[str, Any]:
        """Fallback when API fails."""
        return {
            'data': [],
            'source': 'simulated',
            'note': 'OpenF1 API unavailable - no live position data',
        }
    
    def _fallback_car_data(self, session_key: int, driver_number: int) -> Dict[str, Any]:
        """Fallback when API fails."""
        return {
            'data': [],
            'source': 'simulated',
            'note': 'OpenF1 API unavailable - no car telemetry data',
        }
    
    def _fallback_team_radio(self, session_key: int) -> Dict[str, Any]:
        """Fallback when API fails."""
        return {
            'data': [],
            'source': 'simulated',
            'note': 'OpenF1 API unavailable - no team radio data',
        }
    
    def _fallback_race_control(self, session_key: int) -> Dict[str, Any]:
        """Fallback when API fails."""
        return {
            'data': [],
            'source': 'simulated',
            'note': 'OpenF1 API unavailable - no race control data',
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
                        'source': 'openf1',
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
                        'source': 'openf1',
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
                'source': 'openf1',
                'cache_status': 'error',
                'timestamp': dt.datetime.now().isoformat(),
                'error': str(last_exception)
            }
        }
