"""
System health endpoints — data sources + models
GET /api/v1/system/data-sources
GET /api/v1/system/models
GET /api/v1/system/health
"""
from fastapi import APIRouter
from typing import Any, Dict

router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/data-sources")
async def data_sources():
    try:
        from backend.app.data.providers.registry import registry
        health = await registry.health_all()
    except Exception as e:
        health = {"error": str(e)}
    try:
        from backend.app.cache.redis import get_cache
        cache = get_cache()
        # A DictCache means we silently lost cross-worker coherence.
        backend = type(cache).__name__
        cache_status = {
            "status": "healthy" if backend == "RedisCache" else "degraded",
            "backend": backend,
            **({"reason": "in-memory fallback — not shared across workers"} if backend != "RedisCache" else {}),
        }
    except Exception as e:
        cache_status = {"status": "unavailable", "error": str(e)}
    try:
        from backend.app.database.client import DatabaseClient
        DatabaseClient()  # constructor validates the engine can be built
        db_status = {"status": "healthy"}
    except Exception as e:
        db_status = {"status": "unavailable", "error": str(e)}
    # Top-level, so a client doesn't have to know to dig into providers["overall"].
    overall = health.get("overall", {}) if isinstance(health, dict) else {}
    return {
        "status": overall.get("status", "unknown"),
        "live_providers": overall.get("live_providers", []),
        "note": overall.get("note"),
        "data_sources": health,
        "cache": cache_status,
        "database": db_status,
    }

@router.get("/provenance/{race_id}")
async def provenance(race_id: str, session: str = "race"):
    # Expose the DataProvenance for a race so a client can distinguish a
    # prediction backed by live Jolpica data from one served out of the 2026
    # seed fallback (modify.md section 5, closing the gap named in section 2).
    from fastapi.responses import JSONResponse
    try:
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        if not race:
            return JSONResponse(
                {"error": {"code": "UNKNOWN_RACE", "message": f"Unknown race_id '{race_id}'"}},
                status_code=404,
            )
        from backend.app.data.providers.registry import registry
        _results, prov = await registry.jolpica.get_results(race_id, session)
        _standings, standings_prov = await registry.get_driver_standings(2026)
        return {
            "race_id": race_id,
            "session": session,
            "results": prov.to_dict(),
            "standings": standings_prov.to_dict(),
            "live": prov.cache_status != "fallback",
            "note": (
                "live upstream data" if prov.cache_status != "fallback"
                else "served from fallback/seed — 2026 races that have not happened "
                     "cannot have live results"
            ),
        }
    except Exception as e:
        return JSONResponse(
            {"error": {"code": "PROVENANCE_FAILED", "message": str(e)}}, status_code=500
        )

@router.get("/models")
async def models_health():
    out: Dict[str, Any] = {}
    try:
        import os, json
        reg_path = "training/model_registry/registry.json"
        if os.path.exists(reg_path):
            with open(reg_path) as f:
                reg = json.load(f)
            out["registry"] = reg
        else:
            out["registry"] = {"models": {}, "champion": None, "note": "no registry yet — run training/pipelines/train.py"}
    except Exception as e:
        out["registry_error"] = str(e)
    # check zoo
    try:
        from backend.app.engine.ml_models import model_zoo
        zoo_status = {}
        for name, m in model_zoo.models.items():
            zoo_status[name] = {"is_trained": m.is_trained, "active": name in model_zoo.active_models}
        out["zoo"] = zoo_status
    except Exception as e:
        out["zoo_error"] = str(e)
    # calibrator
    try:
        from backend.app.engine.calibration import probability_calibrator
        out["calibration"] = {"is_fitted": probability_calibrator.is_fitted, "method": probability_calibrator.method}
    except Exception as e:
        out["calibration_error"] = str(e)
    from backend.app.config.settings import settings
    out["versions"] = {"model": getattr(settings,'MODEL_VERSION','12.4'), "feature": getattr(settings,'FEATURE_VERSION','8'), "dataset": getattr(settings,'DATASET_VERSION','14'), "calibration": getattr(settings,'CALIBRATION_VERSION','3.1')}
    return out

@router.get("/health")
async def system_health():
    return {"status": "healthy", "components": ["api","cache","database","providers","models"]}
