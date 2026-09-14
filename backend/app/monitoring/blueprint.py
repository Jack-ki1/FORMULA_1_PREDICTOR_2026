import logging
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/metrics", tags=["monitoring"])
async def metrics():
    if not settings.MONITORING_ENABLED:
        logger.warning("Monitoring disabled, returning empty metrics")
        return Response(content="", media_type=CONTENT_TYPE_LATEST)
    try:
        data = generate_latest()
        logger.info("Metrics endpoint accessed")
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(content="", media_type=CONTENT_TYPE_LATEST)
