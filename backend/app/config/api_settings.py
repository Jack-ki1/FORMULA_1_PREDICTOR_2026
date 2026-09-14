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
    JOLPICA_BASE_URL = os.getenv('JOLPICA_BASE_URL', 'https://api.jolpica.f1')
    OPENF1_BASE_URL = os.getenv('OPENF1_BASE_URL', 'https://api.openf1.org')
    HUGGINGFACE_DATASET = os.getenv('HUGGINGFACE_DATASET', 'tracinginsights/RaceData')
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 2s, 4s, 8s
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]  # Retry on these status codes
    
    # Rate Limiting
    JOLPICA_RATE_LIMIT = 100  # requests per minute
    OPENF1_RATE_LIMIT = 60    # requests per minute
    FASTF1_RATE_LIMIT = 30    # requests per minute
    
    # Timeout Configuration
    DEFAULT_TIMEOUT = 30      # seconds
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
    JOLPICA_ENDPOINTS = {
        'driver_standings': '/f1/{season}/driverStandings.json',
        'constructor_standings': '/f1/{season}/constructorStandings.json',
        'race_result': '/f1/{season}/{round}/results.json',
        'qualifying_result': '/f1/{season}/{round}/qualifying.json',
        'race_schedule': '/f1/{season}.json',
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
