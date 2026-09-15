"""
Settings API — massive tunings control plane.
GET /api/v1/settings — current effective config (sanitized)
POST /api/v1/settings — patch runtime overrides (in-memory, persisted to cache)
POST /api/v1/settings/reset — clear overrides
GET /api/v1/settings/schema — typed schema for frontend
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# In-memory overrides (survives until restart; also mirrored to cache if available)
_overrides: Dict[str, Any] = {}

# Fields that must never be exposed raw
_SENSITIVE = {"SECRET_KEY", "REDIS_PASSWORD", "HUGGINGFACE_API_KEY", "OPENAI_API_KEY", "ALERTING_SLACK_WEBHOOK"}

def _sanitize(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in settings_dict.items():
        if k in _SENSITIVE:
            out[k] = "***" if v else ""
        else:
            out[k] = v
    return out

def _current_settings() -> Dict[str, Any]:
    from backend.app.config.settings import settings
    # Base from pydantic settings model
    base = settings.model_dump() if hasattr(settings, "model_dump") else settings.__dict__.copy()
    # Also include class defaults that may not be in model_dump due to extra allow
    # Merge overrides
    merged = {**base, **_overrides}
    return _sanitize(merged)

@router.get("")
async def get_settings():
    return {
        "settings": _current_settings(),
        "overrides": _sanitize(_overrides),
        "timestamp": time.time(),
        "note": "Runtime overrides are in-memory (and Redis if available) — survive until restart. Env file is source of truth on reboot."
    }

@router.get("/schema")
async def get_schema():
    # Provide frontend with typed schema + groups
    return {
        "groups": [
            {"id": "appearance", "label": "Appearance", "icon": "🎨", "fields": ["THEME", "PRIMARY_COLOR", "BACKGROUND", "SURFACE", "TEXT", "BORDER"]},
            {"id": "engine", "label": "Prediction Engine", "icon": "⚙️", "fields": ["MONTE_CARLO_SIMULATIONS", "SIMULATION_MIN_COUNT", "SIMULATION_MAX_COUNT", "CHAOS_LEVEL_DEFAULT", "WET_INFLUENCE_DEFAULT", "RELIABILITY_INFLUENCE_DEFAULT", "STRATEGY_AGGRESSIVENESS_DEFAULT", "GRID_WEIGHT_DEFAULT", "ENABLE_ENSEMBLE"]},
            {"id": "models", "label": "Models & Versions", "icon": "🧠", "fields": ["DEFAULT_MODEL_VERSION", "MODEL_VERSION", "FEATURE_VERSION", "DATASET_VERSION", "CALIBRATION_VERSION", "MODEL_INFERENCE_OPTIMIZATION_ENABLED", "MODEL_COMPILATION_ENABLED"]},
            {"id": "cache", "label": "Cache & Performance", "icon": "⚡", "fields": ["CACHE_ENABLED", "CACHE_TTL_SECONDS", "CACHE_MAX_SIZE", "CACHE_TTL_SHORT", "CACHE_TTL_LONG", "API_CACHE_TTL", "REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_REQUIRED", "ENABLE_IN_MEMORY_FALLBACK", "API_RESPONSE_COMPRESSION_ENABLED"]},
            {"id": "data", "label": "Data Sources", "icon": "🌐", "fields": ["JOLPICA_BASE_URL", "OPENF1_BASE_URL", "FASTF1_CACHE_ENABLED", "FASTF1_CACHE_PATH", "MODEL_CACHE_PATH", "HUGGINGFACE_DATASET"]},
            {"id": "database", "label": "Database", "icon": "🗄️", "fields": ["DATABASE_URL", "DATABASE_POOL_SIZE", "PREDICTION_RETENTION_DAYS", "SESSION_DATA_RETENTION_HOURS"]},
            {"id": "security", "label": "Security & API", "icon": "🔒", "fields": ["CORS_ORIGINS", "FRONTEND_ORIGIN", "RATE_LIMIT_ENABLED", "RATE_LIMIT_DEFAULT", "RATE_LIMIT_PREDICTIONS", "RATE_LIMIT_AI", "RATE_LIMIT_LIVE", "RATE_LIMIT_EXPORTS", "JWT_ALGORITHM", "JWT_EXPIRATION_HOURS", "INPUT_VALIDATION_ENABLED", "MAX_INPUT_LENGTH"]},
            {"id": "monitoring", "label": "Monitoring", "icon": "📊", "fields": ["MONITORING_ENABLED", "METRICS_PORT", "LOG_AGGREGATION_ENABLED", "LOG_RETENTION_DAYS", "ALERTING_ENABLED"]},
            {"id": "ai", "label": "AI Provider", "icon": "🤖", "fields": ["AI_PROVIDER", "HUGGINGFACE_MODEL_ID", "OPENAI_MODEL", "AI_MODEL_TEMPERATURE", "AI_MODEL_MAX_TOKENS", "AI_MODEL_TOP_P"]},
            {"id": "general", "label": "General", "icon": "🏁", "fields": ["SEASON_YEAR", "DEBUG", "ENVIRONMENT", "VERSION", "LIVE_UPDATE_INTERVAL", "POST_RACE_EVALUATION_ENABLED"]},
        ],
        "sensitive": list(_SENSITIVE),
    }

@router.post("")
async def patch_settings(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": {"code": "INVALID_JSON", "message": "Body must be JSON"}}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": {"code": "INVALID", "message": "Expected object"}}, status_code=400)

    from backend.app.config.settings import settings
    allowed = set(settings.model_dump().keys()) if hasattr(settings, "model_dump") else set(settings.__dict__.keys())
    # Also allow appearance keys that are purely frontend (stored as overrides but not in settings)
    allowed.update({"THEME", "PRIMARY_COLOR", "BACKGROUND", "SURFACE", "TEXT", "BORDER", "THEME_MODE"})
    # Extra frontend-only keys
    extra_allowed = {k for k in body.keys() if k.startswith("FRONTEND_") or k.startswith("UI_")}
    allowed.update(extra_allowed)

    applied = {}
    rejected = []
    for k, v in body.items():
        if k in _SENSITIVE and (not isinstance(v, str) or v == "***"):
            # Don't allow blanking sensitive via masked value
            rejected.append(k)
            continue
        if k not in allowed:
            # Still allow it as generic override (massive tunings = anything)
            # but mark it
            pass
        _overrides[k] = v
        applied[k] = v
        # Also try to set on settings instance for immediate effect where possible
        try:
            if hasattr(settings, k):
                setattr(settings, k, v)
        except Exception:
            pass

    # Try to persist overrides to cache (Redis/Dict) for visibility via health
    try:
        from backend.app.cache.redis import get_cache
        cache = get_cache()
        import json as _json
        cache.set("settings:overrides", _json.dumps(_overrides), ttl=86400)
    except Exception:
        pass

    return {"applied": applied, "rejected_sensitive": rejected, "settings": _current_settings()}

@router.post("/reset")
async def reset_settings():
    _overrides.clear()
    # Also reload from env would revert settings instance? We just clear overrides
    try:
        from backend.app.cache.redis import get_cache
        cache = get_cache()
        cache.set("settings:overrides", "{}", ttl=86400)
    except Exception:
        pass
    return {"reset": True, "settings": _current_settings()}
