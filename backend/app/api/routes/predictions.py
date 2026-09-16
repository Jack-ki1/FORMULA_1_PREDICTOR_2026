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
    # Body size guard first (Tier 6: resource exhaustion via unbounded JSON)
    try:
        raw_body = await request.body()
        if len(raw_body) > 64 * 1024:
            return _error("PAYLOAD_TOO_LARGE", "Request body too large (max 64KB for predictions)", 413, request)
        import json as _json
        data = _json.loads(raw_body) if raw_body else None
    except _json.JSONDecodeError:
        data = None
    except Exception:
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
        # Use threadpool for CPU-bound Monte Carlo at high sim counts (Tier 2: async-ify MC)
        from starlette.concurrency import run_in_threadpool
        sim_count = int(data.get("simulation_count", 10000) or 10000)
        if sim_count > 5000:
            result = await run_in_threadpool(prediction_service.generate, data)
        else:
            result = prediction_service.generate(data)
        latency = time.time() - start
        logger.info("predict race=%s latency=%.3f rid=%s", data.get("race_id"), latency, request.state.request_id)
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

# NOTE: /history/last must be registered BEFORE /history/{race_id}, otherwise
# the path parameter swallows "last" and the literal route is unreachable.
@router.get("/api/v1/predictions/history/last", tags=["predictions"])
async def prediction_history_last(request: Request, simulation_count: int = 2000):
    # Most recent completed race: what actually happened vs what the model said.
    # Powers the Dashboard 'Model vs Last Race' strip. Returns actual: null when
    # there is no recorded result — the UI renders the absence, not a verdict.
    try:
        from backend.app.services.history_service import history_service
        sim = max(200, min(int(simulation_count or 2000), 5000))
        return history_service.last_race(simulation_count=sim)
    except Exception as e:
        logger.exception("prediction history (last) failed")
        return _error("HISTORY_FAILED", str(e), 500, request)

@router.get("/api/v1/predictions/history/{race_id}", tags=["predictions"])
async def prediction_history(race_id: str, request: Request, simulation_count: int = 2000):
    # Actual vs predicted for one race (modify.md section 5).
    try:
        from backend.app.data.calendar_2026 import get_race_by_id
        if not get_race_by_id(race_id):
            return _error("UNKNOWN_RACE", f"Unknown race_id '{race_id}'", 404, request)
        from backend.app.services.history_service import history_service
        sim = max(200, min(int(simulation_count or 2000), 5000))
        return history_service.race_history(race_id, simulation_count=sim)
    except Exception as e:
        logger.exception("prediction history failed")
        return _error("HISTORY_FAILED", str(e), 500, request)
