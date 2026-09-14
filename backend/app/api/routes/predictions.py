import time
import uuid
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from backend.app.services.prediction_service import prediction_service

logger = logging.getLogger(__name__)
router = APIRouter()

def _error(code, msg, status, request: Request, details=None):
    rid = getattr(request.state, "request_id", request.headers.get("X-Request-ID") or str(uuid.uuid4()))
    return JSONResponse({"error": {"code": code, "message": msg, "details": details or {}, "request_id": rid}}, status_code=status)

async def _handle_predict(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = None
    if not data:
        return _error("INVALID_JSON", "Request body must be JSON", 400, request)
    if not data.get("race_id"):
        return _error("MISSING_RACE_ID", "race_id is required", 400, request)
    start = time.time()
    try:
        result = prediction_service.generate(data)
        latency = time.time() - start
        logger.info(f"predict race=%s latency=%.3f rid=%s", data.get("race_id"), latency, request.state.request_id)
        return JSONResponse(content=result, headers={"X-Prediction-Latency": f"{latency:.3f}", "X-Request-ID": request.state.request_id})
    except ValueError as e:
        return _error("VALIDATION_ERROR", str(e), 400, request)
    except Exception as e:
        logger.exception("prediction failed")
        return _error("PREDICTION_FAILED", "Prediction generation failed", 500, request, {"exception": str(e)})

@router.post("/api/v1/predictions", tags=["predictions"])
@router.post("/api/v1/predict", tags=["predictions"])
@router.post("/api/v1/predict-session", tags=["predictions"])
async def predict(request: Request):
    return await _handle_predict(request)
