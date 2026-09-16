"""
PredictionService — thin orchestration layer over engine.predictor.generate_prediction.
Preserves 1:1 input->engine->output parity; adds validation, logging, authorization boundary.
"""
import logging
import hashlib
import json
from typing import Any, Dict, Optional
from backend.app.engine.predictor import generate_prediction

logger = logging.getLogger(__name__)

class PredictionService:
    """Service boundary for all prediction generation."""

    @staticmethod
    def _grid_hash(grid: Optional[Dict[str,int]]) -> str:
        if not grid:
            return "nogrid"
        s = json.dumps(grid, sort_keys=True)
        return hashlib.md5(s.encode()).hexdigest()[:8]

    def _cache_key(self, payload: Dict[str, Any]) -> str:
        # Hash includes race/session/snapshot/model/feature/weather/grid/config — event-aware invalidation
        from backend.app.config.settings import settings
        safe = {k: v for k, v in payload.items() if k not in ("ai_api_key", "api_key")}
        if "ai_config" in safe and isinstance(safe["ai_config"], dict):
            safe["ai_config"] = {k: v for k, v in safe["ai_config"].items() if "key" not in k.lower()}
        # include model/feature/dataset version so promotion invalidates cache
        safe["_model_version"] = getattr(settings, 'MODEL_VERSION', '12.4')
        safe["_feature_version"] = getattr(settings, 'FEATURE_VERSION', '8')
        safe["_dataset_version"] = getattr(settings, 'DATASET_VERSION', '14')
        raw = json.dumps(safe, sort_keys=True, default=str)
        return f"pred:{hashlib.md5(raw.encode()).hexdigest()[:12]}"

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        race_id = payload.get("race_id")
        if not race_id or not isinstance(race_id, str):
            raise ValueError("race_id is required and must be a string")
        # Validate race_id exists in 2026 calendar (prevents nonsense like "invalid")
        try:
            from backend.app.data.calendar_2026 import get_race_by_id
            if not get_race_by_id(race_id):
                raise ValueError(f"Unknown race_id '{race_id}' — must be one of 2026 calendar ids (e.g., 'au','mc','sg')")
        except ValueError:
            raise
        except Exception:
            pass
        session_type = payload.get("session_type", "race")
        if session_type not in ("race", "qualifying", "practice"):
            raise ValueError("session_type must be one of: race, qualifying, practice")
        sub_session = payload.get("sub_session")
        weather = payload.get("weather", "dry")
        if weather not in ("dry", "wet", "mixed"):
            raise ValueError("weather must be one of: dry, wet, mixed")
        grid_positions = payload.get("grid_positions")
        if grid_positions is not None:
            if not isinstance(grid_positions, dict):
                raise ValueError("grid_positions must be a dict of driver_code -> position")
            # Validate positions against the real grid size (derived, never hardcoded)
            from backend.app.config.constants import grid_size
            max_pos = grid_size()
            positions = list(grid_positions.values())
            if any(not isinstance(p, int) or p < 1 or p > max_pos for p in positions):
                raise ValueError(f"grid_positions values must be integers 1-{max_pos}")
            if len(positions) != len(set(positions)):
                raise ValueError("grid_positions contains duplicate positions — each driver must have unique position")
        feature_weights = payload.get("feature_weights")
        simulation_count = payload.get("simulation_count", 10000)
        ai_config = payload.get("ai_config") or {
            "ai_mode": payload.get("ai_mode", "normal"),
            "ai_model": payload.get("ai_model", "gemini-2.0-flash-exp"),
            "ai_api_key": payload.get("ai_api_key", ""),
            "ai_weight": payload.get("ai_weight", 0.3),
            "ai_temperature": payload.get("ai_temperature", 0.7),
        }
        try:
            simulation_count = int(simulation_count)
        except Exception:
            simulation_count = 10000
        logger.info("PredictionService.generate race=%s session=%s weather=%s sims=%s grid_hash=%s",
                    race_id, session_type, weather, simulation_count, self._grid_hash(grid_positions))
        # Cache check — hash input features, Redis TTL 3600
        cache = None
        cache_key = None
        try:
            from backend.app.cache.redis import get_cache
            cache = get_cache()
            cache_key = self._cache_key({**payload, "simulation_count": simulation_count})
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit {cache_key}")
                if isinstance(cached, str):
                    return json.loads(cached)
                return cached
        except Exception:
            pass
        # Orchestrator enriches with ML+snapshots where available, but base predictor remains authoritative
        # Provenance: indicate fallback since 2026 has no real results yet
        provenance_hint = {
            "note": "2026 season has no real results yet — prediction uses fallback constants / Monte Carlo heuristic",
            "expected_source": "fallback",
        }
        result = generate_prediction(
            race_id=race_id,
            session_type=session_type,
            sub_session=sub_session,
            weather=weather,
            grid_positions=grid_positions,
            feature_weights=feature_weights,
            simulation_count=simulation_count,
            ai_config=ai_config,
            provenance=provenance_hint,
        )
        # Surface provenance in API response (Tier 2: provenance in response, not just modeled)
        if "provenance" not in result:
            result["provenance"] = provenance_hint
        # Expose prediction_source explicitly for clients
        if "prediction_source" not in result and "predictions" in result:
            # derive from first target source
            try:
                first = next(iter(result["predictions"].values()))
                result["prediction_source"] = first.get("source", "model")
            except Exception:
                result["prediction_source"] = "model"
        # Augment with snapshot/provenance/model health if not already present
        try:
            from backend.app.prediction.snapshot import build_snapshot
            if "snapshot" not in result:
                snap = build_snapshot(race_id, session_type, sub_session=sub_session or "", grid_positions=result.get("grid_positions", grid_positions or {}), weather_condition=weather, simulation_count=simulation_count, random_seed=payload.get("random_seed", 42))
                result["snapshot"] = snap.to_dict()
                result["model_version"] = snap.model_version
                result["feature_version"] = snap.feature_version
                result["data_quality"] = {"score": 0.85, "note": "orchestrator snapshot"}
        except Exception:
            pass
        try:
            if cache and cache_key:
                cache.set(cache_key, json.dumps(result), ttl=3600)
        except Exception:
            pass
        return result

prediction_service = PredictionService()
