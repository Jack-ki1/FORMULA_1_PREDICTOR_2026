"""
API settings and configuration for external data sources.
Includes base URLs, rate limits, retry logic, and connection settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class APISettings:
    """Configuration for external API integrations."""
    
    # Base URLs
    # NOTE: the default used to be 'https://api.jolpica.f1', which is NOT a real
    # domain — DNS fails instantly, so every standings/qualifying request burned
    # the full retry backoff (time.sleep(1) + time.sleep(2) = 3s) before falling
    # back to data it already had locally. Per-request cost measured at 3.1s,
    # 97% of it in time.sleep. The Ergast-compatible Jolpica API lives at
    # api.jolpi.ca and answers 2026 queries in ~1s (verified).
    JOLPICA_BASE_URL = os.getenv('JOLPICA_BASE_URL', 'https://api.jolpi.ca')
    OPENF1_BASE_URL = os.getenv('OPENF1_BASE_URL', 'https://api.openf1.org')
    HUGGINGFACE_DATASET = os.getenv('HUGGINGFACE_DATASET', 'tracinginsights/RaceData')
    
    # Retry Configuration
    MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '2'))
    RETRY_BACKOFF_FACTOR = float(os.getenv('API_RETRY_BACKOFF_FACTOR', '0.5'))
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]  # Retry on these status codes

    # Circuit breaker: after this many consecutive *connection* failures the
    # client stops attempting the network for COOLDOWN seconds and serves the
    # local/fallback path immediately. Without this, an unreachable or slow
    # upstream costs every single request the full retry backoff — which is
    # exactly the 3s-per-call regression this fixes.
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv('API_CIRCUIT_BREAKER_THRESHOLD', '2'))
    CIRCUIT_BREAKER_COOLDOWN = float(os.getenv('API_CIRCUIT_BREAKER_COOLDOWN', '300'))
    
    # Rate Limiting
    JOLPICA_RATE_LIMIT = 100  # requests per minute
    OPENF1_RATE_LIMIT = 60    # requests per minute
    FASTF1_RATE_LIMIT = 30    # requests per minute
    
    # Timeout Configuration
    # Kept short deliberately: this is a UI-facing API. A slow upstream must not
    # hold the request open — we would rather fall back to local data fast.
    DEFAULT_TIMEOUT = float(os.getenv('API_DEFAULT_TIMEOUT', '6'))
    CONNECT_TIMEOUT = float(os.getenv('API_CONNECT_TIMEOUT', '3'))
    LONG_TIMEOUT = 120        # seconds for large data fetches
    
    # Cache Configuration
    ENABLE_CACHING = True
    CACHE_TTL_DEFAULT = 300   # 5 minutes
    CACHE_TTL_LONG = 3600     # 1 hour for static data
    CACHE_TTL_SHORT = 60      # 1 minute for live data
    
    # Feature Flags
    ENABLE_JOLPICA = True
    ENABLE_OPENF1 = True     # Set to False if API is unavailable
    ENABLE_FASTF1 = True     # Set to False if you don't need telemetry
    ENABLE_HUGGINGFACE = False  # Optional: set to True for historical data
    
    # API-specific Endpoints
    # Jolpica serves the Ergast-compatible surface under /ergast, so every path
    # here must carry that prefix. Without it these requests 404 on the bare host
    # and silently fall back to local data — which is why "live" standings never
    # actually loaded (verified: https://api.jolpi.ca/f1/2026/... -> 404,
    # https://api.jolpi.ca/ergast/f1/2026/... -> 200).
    JOLPICA_ENDPOINTS = {
        'driver_standings': '/ergast/f1/{season}/driverStandings.json',
        'constructor_standings': '/ergast/f1/{season}/constructorStandings.json',
        'race_result': '/ergast/f1/{season}/{round}/results.json',
        'qualifying_result': '/ergast/f1/{season}/{round}/qualifying.json',
        'race_schedule': '/ergast/f1/{season}.json',
    }
    
    OPENF1_ENDPOINTS = {
        'sessions': '/v1/sessions',
        'drivers': '/v1/drivers',
        'team_radio': '/v1/team_radio',
        'race_control': '/v1/race_control',
        'position': '/v1/position',
        'car_data': '/v1/car_data',
    }
    
    @classmethod
    def get_endpoint(cls, api_name, endpoint_key, **params):
        """Get formatted endpoint URL with parameters."""
        if api_name == 'jolpica':
            template = cls.JOLPICA_ENDPOINTS.get(endpoint_key)
            if template:
                return cls.JOLPICA_BASE_URL + template.format(**params)
        elif api_name == 'openf1':
            endpoint = cls.OPENF1_ENDPOINTS.get(endpoint_key)
            if endpoint:
                return cls.OPENF1_BASE_URL + endpoint
        return None
    
    @classmethod
    def is_enabled(cls, api_name):
        """Check if an API integration is enabled."""
        return {
            'jolpica': cls.ENABLE_JOLPICA,
            'openf1': cls.ENABLE_OPENF1,
            'fastf1': cls.ENABLE_FASTF1,
            'huggingface': cls.ENABLE_HUGGINGFACE,
        }.get(api_name.lower(), False)

# Global API settings instance
api_settings = APISettings()
