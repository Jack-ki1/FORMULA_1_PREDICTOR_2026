from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()

@router.get("/api/v1/health", tags=["health"])
async def health_v1():
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}
