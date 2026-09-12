import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify
from config.settings import settings
from database.client import DatabaseClient
from security.auth import require_auth
from security.middleware import add_security_headers

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


def check_database_health() -> dict:
    """Check database health and return status."""
    try:
        db_client = DatabaseClient()
        stats = db_client.get_database_stats()
        
        # Check if database is responsive
        if 'error' in stats:
            return {
                'status': 'unhealthy',
                'database': 'unavailable',
                'error': stats['error']
            }
        
        return {
            'status': 'healthy',
            'database': 'available',
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'database': 'unavailable',
            'error': str(e)
        }

@health_bp.route('/health')
@add_security_headers
@require_auth
def health_check():
    """Health check endpoint."""
    try:
        # Basic application health
        app_health = {
            'status': 'healthy',
            'version': settings.VERSION,
            'environment': settings.ENVIRONMENT,
            'timestamp': str(datetime.now(timezone.utc))
        }
        
        # Database health check
        db_health = check_database_health()
        
        # Combine results
        health_status = {
            'app': app_health,
            'database': db_health,
            'overall_status': 'healthy' if app_health['status'] == 'healthy' and db_health['status'] == 'healthy' else 'unhealthy'
        }
        
        logger.info(f"Health check completed: {health_status['overall_status']}")
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503