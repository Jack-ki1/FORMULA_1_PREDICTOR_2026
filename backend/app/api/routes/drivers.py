import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.data.driver_data import get_all_enhanced_drivers, get_driver_bio

router = APIRouter()

def _error(code, msg, status, request: Request):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "request_id": rid}}, status_code=status)

@router.get("/api/v1/drivers", tags=["drivers"])
async def list_drivers(request: Request):
    """Get all drivers with enhanced biographical data."""
    try:
        drivers = get_all_enhanced_drivers()
        return JSONResponse(content={"drivers": drivers})
    except Exception as e:
        return _error("DRIVERS_FAILED", str(e), 500, request)

@router.get("/api/v1/drivers/{driver_code}", tags=["drivers"])
async def get_driver(driver_code: str, request: Request):
    """Get specific driver biography."""
    try:
        bio = get_driver_bio(driver_code.upper())
        if not bio:
            return _error("DRIVER_NOT_FOUND", f"Driver {driver_code} not found", 404, request)
        return JSONResponse(content=bio)
    except Exception as e:
        return _error("DRIVER_FAILED", str(e), 500, request)
