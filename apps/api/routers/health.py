from datetime import datetime, timezone

from fastapi import APIRouter

from config.settings import settings
from database.db import verify_connection

router = APIRouter()


@router.get("/health")
def health():
    db_ok = verify_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "version": settings.VERSION,
        "database": "connected" if db_ok else "unreachable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
