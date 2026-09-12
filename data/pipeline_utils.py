from typing import Dict, Any, Optional
import datetime as dt


def get_data_source_info(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract source information from data dictionary."""
    if 'provenance' in data:
        return {
            'source': data['provenance'].get('source', 'unknown'),
            'cache_status': data['provenance'].get('cache_status', 'unknown'),
            'timestamp': data['provenance'].get('timestamp', 'unknown')
        }
    elif 'source' in data:
        return {
            'source': data['source'],
            'cache_status': 'unknown',
            'timestamp': 'unknown'
        }
    else:
        return {
            'source': 'unknown',
            'cache_status': 'unknown',
            'timestamp': 'unknown'
        }

def is_cached_data(data: Dict[str, Any]) -> bool:
    """Check if data is from cache."""
    source_info = get_data_source_info(data)
    return source_info['cache_status'] == 'hit'

def get_pipeline_stats() -> Dict[str, Any]:
    """Get statistics about pipeline usage."""
    return {
        'total_requests': 0,
        'cache_hits': 0,
        'validation_failures': 0,
        'normalization_successes': 0,
        'last_run': dt.datetime.now().isoformat()
    }

def log_pipeline_event(event_type: str, data_type: str, duration: float, success: bool = True, error: Optional[str] = None):
    """Log pipeline processing events."""
    # This would integrate with the logging system
    pass

def validate_pipeline_configuration(config: Dict[str, Any]) -> bool:
    """Validate pipeline configuration."""
    required_keys = ['enable_validation', 'enable_normalization', 'enable_provenance_tracking']
    return all(key in config for key in required_keys)