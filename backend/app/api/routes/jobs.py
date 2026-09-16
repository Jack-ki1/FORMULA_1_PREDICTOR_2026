"""
Async jobs — POST /api/v1/predictions/jobs
Jobs run via in-memory queue (Redis-backed where available). For demo, runs synchronously but returns job envelope.
"""
from fastapi import APIRouter
import uuid, time
from typing import Any, Dict

router = APIRouter(prefix="/api/v1", tags=["jobs"])

_jobs: Dict[str, Dict[str,Any]] = {}

@router.post("/predictions/jobs")
async def create_job(payload: Dict[str, Any]):
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    _jobs[job_id] = {"job_id": job_id, "status": "queued", "payload": payload, "created_at": time.time()}
    # try to run immediately for small sims; large sims would be worker
    sims = int(payload.get("simulation_count", 5000))
    if sims <= 10000:
        try:
            from backend.app.engine.predictor import generate_prediction
            result = generate_prediction(race_id=payload.get("race_id","au"), session_type=payload.get("session_type","race"), weather=payload.get("weather","dry"), grid_positions=payload.get("grid_positions"), simulation_count=sims)
            _jobs[job_id].update({"status": "completed", "result": result})
        except Exception as e:
            _jobs[job_id].update({"status": "failed", "error": str(e)})
    else:
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["note"] = "Large simulation — worker would process; demo returns queued"
    return {"job_id": job_id, "status": _jobs[job_id]["status"]}

@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error":{"code":"NOT_FOUND","message":f"job {job_id} not found"}}, status_code=404)
    return job
