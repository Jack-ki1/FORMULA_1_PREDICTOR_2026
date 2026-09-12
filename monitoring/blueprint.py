import logging
from flask import Blueprint, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from config.settings import settings
from monitoring.metrics import app_requests_total, app_request_duration_seconds

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/metrics')
def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        Response containing Prometheus metrics in text format
    """
    if not settings.MONITORING_ENABLED:
        logger.warning("Monitoring disabled, returning empty metrics")
        return Response('', mimetype=CONTENT_TYPE_LATEST)
    
    try:
        # Generate latest metrics
        metrics_data = generate_latest()
        
        logger.info("Metrics endpoint accessed")
        return Response(metrics_data, mimetype=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response('', mimetype=CONTENT_TYPE_LATEST)