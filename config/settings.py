"""
Application settings and configuration.
Central point for all environment-based configuration.
"""
import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Season Configuration
    SEASON_YEAR: int = 2026
    DEBUG: bool = False
    
    # Application Configuration
    VERSION: str = '1.0.0'
    ENVIRONMENT: str = 'development'
    HOST: str = '0.0.0.0'
    PORT: int = 5000
    
    # Flask Configuration
    SECRET_KEY: str = 'dev-secret-key-change-in-production'
    FLASK_ENV: str = 'development'
    FLASK_HOST: str = '0.0.0.0'
    FLASK_PORT: int = 5000
    
    # Cache Configuration
    API_CACHE_TTL: int = 300  # 5 minutes default
    CACHE_TTL_SHORT: int = 60  # 1 minute
    CACHE_TTL_LONG: int = 3600  # 1 hour
    API_RESPONSES_CACHE: str = 'cache/api_responses'
    FASTF1_CACHE_ENABLED: bool = True
    FASTF1_CACHE_PATH: str = 'cache/fastf1_cache'
    MODEL_CACHE_PATH: str = 'cache/model_cache'
    
    # Database configuration
    DATABASE_URL: str = 'sqlite:///./f1_predictions.db'
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: float = 30.0
    DATABASE_POOL_RECYCLE: int = 1800

    # Data retention policies
    PREDICTION_RETENTION_DAYS: int = 90
    SESSION_DATA_RETENTION_HOURS: int = 24
    ERROR_LOG_RETENTION_DAYS: int = 30

    # Database health check
    DATABASE_HEALTH_CHECK_INTERVAL: int = 300  # 5 minutes

    # Background Scheduler
    LIVE_UPDATE_INTERVAL: int = 300  # 5 minutes
    POST_RACE_EVALUATION_ENABLED: bool = True
    
    # Model Configuration
    DEFAULT_MODEL_VERSION: str = 'v1.0'
    ENABLE_ENSEMBLE: bool = True
    MONTE_CARLO_SIMULATIONS: int = 1000
    SIMULATION_MIN_COUNT: int = 100
    SIMULATION_MAX_COUNT: int = 10000

    # AI provider configuration
    AI_PROVIDER: str = 'huggingface'
    HUGGINGFACE_API_KEY: str = ''
    OPENAI_API_KEY: str = ''
    HUGGINGFACE_MODEL_ID: str = 'microsoft/phi-2'
    OPENAI_MODEL: str = 'gpt-3.5-turbo-instruct'

    # AI model configuration
    AI_MODEL_TEMPERATURE: float = 0.7
    AI_MODEL_MAX_TOKENS: int = 100
    AI_MODEL_TOP_P: float = 0.9

    # Security configuration
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = 24

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = '100/hour'
    RATE_LIMIT_AUTHED: str = '500/hour'

    # Security headers
    SECURITY_HEADERS: Dict[str, str] = {
        'Content-Security-Policy': "default-src 'self'",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }

    # Input validation settings
    INPUT_VALIDATION_ENABLED: bool = True
    MAX_INPUT_LENGTH: int = 1000

    # Monitoring and observability configuration
    MONITORING_ENABLED: bool = True
    METRICS_PORT: int = 9090
    METRICS_UPDATE_INTERVAL: int = 15

    # Log aggregation configuration
    LOG_AGGREGATION_ENABLED: bool = True
    LOG_RETENTION_DAYS: int = 30

    # Alerting configuration
    ALERTING_ENABLED: bool = True
    ALERTING_EMAIL_RECIPIENTS: List[str] = []
    ALERTING_SLACK_WEBHOOK: str = ''

    # Custom metrics configuration
    PREDICTION_LATENCY_BUCKETS: List[float] = [0.1, 0.5, 1.0, 2.0, 5.0]
    DATABASE_QUERY_LATENCY_BUCKETS: List[float] = [0.01, 0.05, 0.1, 0.5]

    # Performance optimization configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_SIZE: int = 1000
    
    # Redis configuration
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Database optimization
    DATABASE_QUERY_OPTIMIZATION_ENABLED: bool = True
    DATABASE_INDEXES_ENABLED: bool = True

    # ML model optimization
    MODEL_INFERENCE_OPTIMIZATION_ENABLED: bool = True
    MODEL_COMPILATION_ENABLED: bool = False

    # API response optimization
    API_RESPONSE_COMPRESSION_ENABLED: bool = True
    API_RESPONSE_CACHE_HEADERS: str = 'public, max-age=300'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='allow'
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Database configuration validation
        if self.DATABASE_URL.startswith('sqlite') and not self.DATABASE_URL.startswith('sqlite:///'):
            raise ValueError("SQLite DATABASE_URL must start with 'sqlite:///'")

        # Initialize directories
        self._init_directories()

    def _init_directories(self):
        """Initialize required directories."""
        import os
        directories = [
            self.FASTF1_CACHE_PATH,
            self.MODEL_CACHE_PATH,
            'cache/api_responses',
            'cache/fastf1_cache',
            'cache/model_cache'
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

# Create settings instance
settings = Settings()