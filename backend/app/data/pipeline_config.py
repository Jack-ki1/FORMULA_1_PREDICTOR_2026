from typing import Dict, Any
from backend.app.config.settings import settings


class PipelineConfig:
    """Configuration for the centralized data pipeline."""
    
    # Pipeline step configuration
    ENABLE_VALIDATION = True
    ENABLE_NORMALIZATION = True
    ENABLE_PROVENANCE_TRACKING = True
    
    # Validation configuration
    VALIDATION_LEVELS = {
        'standings': 'strict',
        'grid': 'strict',
        'weather': 'medium',
        'lap_times': 'medium',
        'session_results': 'strict'
    }
    
    # Normalization configuration
    NORMALIZATION_STRATEGIES = {
        'standings': 'jolpica_openf1_unified',
        'grid': 'qualifying_position_mapping',
        'weather': 'fastf1_openf1_unified',
        'lap_times': 'fastf1_standardized',
        'session_results': 'race_result_standardized'
    }
    
    # Provenance configuration
    PROVENANCE_LEVEL = 'detailed'  # 'minimal', 'standard', 'detailed'
    
    @classmethod
    def get_pipeline_config(cls) -> Dict[str, Any]:
        """Get complete pipeline configuration."""
        return {
            'enable_validation': cls.ENABLE_VALIDATION,
            'enable_normalization': cls.ENABLE_NORMALIZATION,
            'enable_provenance_tracking': cls.ENABLE_PROVENANCE_TRACKING,
            'validation_levels': cls.VALIDATION_LEVELS,
            'normalization_strategies': cls.NORMALIZATION_STRATEGIES,
            'provenance_level': cls.PROVENANCE_LEVEL,
            'cache_ttl': {
                'standings': settings.CACHE_TTL_LONG,
                'grid': settings.CACHE_TTL_SHORT,
                'weather': settings.CACHE_TTL_SHORT,
                'lap_times': settings.CACHE_TTL_SHORT,
                'session_results': settings.CACHE_TTL_LONG
            }
        }