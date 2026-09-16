"""
Generic HTTP client with retries, backoff, and response caching.
Serves as the base for all API integrations.
"""
import requests
import time
import json
import hashlib
import os
import datetime as dt
from datetime import timedelta
from typing import Optional, Dict, Any
from backend.app.config.settings import settings
from backend.app.config.api_settings import api_settings


class APIClient:
    """Generic API client with retry logic and caching."""
    
    # Circuit breaker shared across ALL instances of a host. Class-level on
    # purpose: the client is re-instantiated per request (e.g. JolpicaClient()),
    # so per-instance state would never accumulate and the breaker would never
    # trip. Keyed by base_url.
    _breaker_failures: Dict[str, int] = {}
    _breaker_open_until: Dict[str, float] = {}

    def __init__(self, base_url: str, cache_enabled: bool = True):
        self.base_url = base_url.rstrip('/')
        self.cache_enabled = cache_enabled
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'F1-Predictor-2026/1.0',
            'Accept': 'application/json',
        })

    # ---- circuit breaker -------------------------------------------------
    def _breaker_is_open(self) -> bool:
        return time.time() < self._breaker_open_until.get(self.base_url, 0.0)

    def _breaker_record_failure(self) -> None:
        n = self._breaker_failures.get(self.base_url, 0) + 1
        self._breaker_failures[self.base_url] = n
        if n >= api_settings.CIRCUIT_BREAKER_THRESHOLD:
            self._breaker_open_until[self.base_url] = time.time() + api_settings.CIRCUIT_BREAKER_COOLDOWN

    def _breaker_record_success(self) -> None:
        self._breaker_failures[self.base_url] = 0
        self._breaker_open_until.pop(self.base_url, None)
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from URL and parameters."""
        key_string = f"{url}_{json.dumps(params, sort_keys=True) if params else ''}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get cache file path for a cache key."""
        return os.path.join(settings.API_RESPONSES_CACHE, f"{cache_key}.json")

    def _build_url(self, endpoint: str) -> str:
        """Accept either a relative endpoint or a fully-qualified endpoint.

        Jolpica exposes the Ergast-compatible surface under `/ergast`, so a
        caller passing `/f1/2026/driverStandings.json` must be resolved to
        `<base>/ergast/f1/2026/driverStandings.json`. Without this the requests
        hit the bare host, got 404, and fell back — which is why live standings
        never actually loaded. A caller that already includes the prefix, or
        passes a fully-qualified URL, is left untouched.
        """
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        path = endpoint.lstrip('/')
        if path.startswith('ergast/'):
            return f"{self.base_url}/{path}"
        return f"{self.base_url}/ergast/{path}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available and not expired."""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(cache_key)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Check if cache is expired
            cached_time = dt.datetime.fromisoformat(cached_data.get('timestamp', ''))
            ttl = cached_data.get('ttl', api_settings.CACHE_TTL_DEFAULT)
            
            if dt.datetime.now() - cached_time < timedelta(seconds=ttl):
                payload = cached_data.get('data')
                # A cached payload carrying no usable records is worse than no
                # cache at all: it is served as `source: cached` forever, so the
                # UI shows an EMPTY driver list while every upstream call is
                # skipped. That is exactly what happened when the Jolpica base
                # URL was wrong - the empty result was written to disk and then
                # trusted indefinitely.
                if not self._is_usable_payload(payload):
                    try:
                        os.remove(cache_path)
                    except OSError:
                        pass
                    return None
                return payload
            else:
                # Remove expired cache
                os.remove(cache_path)
                return None
        except (json.JSONDecodeError, KeyError, ValueError, TypeError, OSError):
            return None
    
    @staticmethod
    def _is_usable_payload(data: Any) -> bool:
        """Reject payloads that would degrade the UI if served from cache.

        An error dict, an empty list, or a standings-shaped response with no
        entries are all 'negative results'. Caching them turns a transient
        upstream failure into a permanent one.
        """
        if data is None:
            return False
        if isinstance(data, dict):
            if data.get('error') or data.get('fallback'):
                return False
            # A recognised content key that is present-but-empty is a negative
            # result. Check emptiness of CONTENT, not the number of keys — a
            # single-key payload like {'standings': [...]} is perfectly valid.
            content_keys = ('standings', 'races', 'results', 'data', 'items', 'news')
            present = [k for k in content_keys if k in data]
            if present and all(
                not data.get(k) for k in present
            ):
                return False
            return True
        if isinstance(data, list):
            return len(data) > 0
        return True

    def _cache_response(self, cache_key: str, data: Any, ttl: int = None):
        """Cache response with timestamp and TTL."""
        if not self.cache_enabled:
            return
        
        cache_path = self._get_cache_path(cache_key)
        ttl = ttl or api_settings.CACHE_TTL_DEFAULT
        # Never persist a negative result - see _is_usable_payload.
        if not self._is_usable_payload(data):
            return
        
        cache_data = {
            'timestamp': dt.datetime.now().isoformat(),
            'ttl': ttl,
            'data': data,
        }
        
        try:
            os.makedirs(settings.API_RESPONSES_CACHE, exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
        except (IOError, json.JSONDecodeError):
            pass  # Fail silently if caching fails
    
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
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            timeout: Request timeout in seconds
            use_cache: Whether to use caching
            cache_ttl: Cache time-to-live in seconds
        
        Returns:
            Response data as dictionary
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
                    'cached_at': self._get_cache_path(cache_key),
                }
        
        # Circuit breaker: if this host has been failing, do NOT attempt the
        # network at all. This is what turns a permanently-broken upstream from
        # "3s on every request" into "instant fallback". (Measured: 97% of a
        # standings request was time.sleep from retry backoff against a
        # non-existent host.)
        if self._breaker_is_open():
            return {
                'data': None,
                'source': 'fallback',
                'error': f'circuit breaker open for {self.base_url} '
                         f'(skipped network, serving local/fallback)',
                'breaker_open': True,
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
                    timeout=(api_settings.CONNECT_TIMEOUT, timeout),
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Cache successful GET responses
                if method.upper() == 'GET' and use_cache:
                    self._cache_response(cache_key, response_data, cache_ttl)
                
                self._breaker_record_success()
                return {
                    'data': response_data,
                    'source': 'live',
                    'status_code': response.status_code,
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
                # Connection-level failures (DNS, refused, timeout) are what the
                # breaker tracks. A rate-limit or 5xx is handled above.
                self._breaker_record_failure()
                # Do NOT sleep-and-retry a name-resolution failure: retrying
                # cannot help and the backoff is pure user-facing latency.
                if isinstance(e, (requests.exceptions.ConnectionError,
                                  requests.exceptions.InvalidURL)):
                    break

            # Exponential backoff (reduced default: 0.5s, 1s)
            if attempt < api_settings.MAX_RETRIES - 1:
                backoff_time = api_settings.RETRY_BACKOFF_FACTOR ** attempt
                time.sleep(backoff_time)

        # All retries failed
        return {
            'data': None,
            'source': 'error',
            'error': str(last_exception),
        }
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict:
        """Make GET request."""
        return self._make_request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict:
        """Make POST request."""
        return self._make_request('POST', endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict:
        """Make PUT request."""
        return self._make_request('PUT', endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict:
        """Make DELETE request."""
        return self._make_request('DELETE', endpoint, **kwargs)
    
    def clear_cache(self):
        """Clear all cached responses for this client."""
        if not self.cache_enabled:
            return
        
        try:
            for filename in os.listdir(settings.API_RESPONSES_CACHE):
                file_path = os.path.join(settings.API_RESPONSES_CACHE, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except OSError:
            pass
