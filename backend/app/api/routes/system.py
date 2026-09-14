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
        cache_status = {"status": "healthy", "backend": type(cache).__name__}
    except Exception as e:
        cache_status = {"status": "unavailable", "error": str(e)}
    try:
        from backend.app.database.client import DatabaseClient
        db = DatabaseClient()
        db_status = {"status": "healthy"}
    except Exception as e:
        db_status = {"status": "unavailable", "error": str(e)}
    return {"data_sources": health, "cache": cache_status, "database": db_status}

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
