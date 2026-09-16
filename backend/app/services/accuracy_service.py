"""
AccuracyService — measures the model against recorded race results.

This is the *real* counterpart to the hardcoded `TARGETS[...]['accuracy']`
constants that `/api/v1/analytics/accuracy` used to serve as if they were
measurements (see `benchmark_suite.generate_accuracy_report`).

Design rules, deliberately:
  * It measures by running the actual production predictor on each completed
    race and comparing to the recorded classification.
  * If there is not enough history it returns `accuracy: None` and
    `status: "insufficient_data"`. It NEVER invents a number, and never falls
    back to a constant.
  * Results are memoised in-process so the endpoint does not re-run 14 races on
    every request.

Backs GET /api/v1/analytics/accuracy.
"""
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Memoisation: measuring runs the predictor once per completed race, which is
# real CPU work. Keyed on (target set, race count, sim count) and held in-process.
_CACHE: Dict[Tuple, Tuple[float, Dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 3600
_CACHE_LOCK = threading.Lock()

DEFAULT_SIMULATION_COUNT = 1200
MIN_RACES_FOR_MEASUREMENT = 3


def _completed_races() -> List[Tuple[str, int]]:
    """(race_id, round) for every round that has a recorded result, in order."""
    try:
        from backend.app.data.calendar_2026 import CALENDAR_2026
        from backend.app.data.season_2026 import SEASON_2026_RESULTS
        done = set(SEASON_2026_RESULTS.get("results", {}).keys())
        return [(r.get("id"), r.get("round")) for r in CALENDAR_2026 if r.get("round") in done]
    except Exception as e:
        logger.warning("completed race scan failed: %s", e)
        return []


def _actual_for_round(round_number: int) -> Optional[Dict[str, Any]]:
    try:
        from backend.app.data.season_2026 import get_race_result
        return get_race_result(round_number)
    except Exception:
        return None


def _score_race(race_id: str, simulation_count: int) -> Optional[Dict[str, Any]]:
    """Run the predictor once for a race and return per-target correctness."""
    try:
        from backend.app.engine.predictor import generate_prediction
        res = generate_prediction(race_id, "race", simulation_count=simulation_count)
        preds = res.get("predictions", {})
        winner_list = (preds.get("winner", {}) or {}).get("predictions", [])
        podium_list = (preds.get("podium", {}) or {}).get("predictions", [])
        points_list = (preds.get("points", {}) or {}).get("predictions", [])
        return {
            "winner": winner_list[0]["driver_code"] if winner_list else None,
            "podium": [p["driver_code"] for p in podium_list[:3]],
            "points": [p["driver_code"] for p in points_list[:10]],
        }
    except Exception as e:
        logger.warning("_score_race(%s) failed: %s", race_id, e)
        return None


def measure_accuracy(simulation_count: int = DEFAULT_SIMULATION_COUNT,
                     force: bool = False) -> Dict[str, Any]:
    """Measure winner/podium/points hit-rates across completed races."""
    races = _completed_races()
    cache_key = (len(races), simulation_count)

    with _CACHE_LOCK:
        hit = _CACHE.get(cache_key)
        if hit and not force and (time.time() - hit[0]) < _CACHE_TTL_SECONDS:
            return hit[1]

    if len(races) < MIN_RACES_FOR_MEASUREMENT:
        result = {
            "status": "insufficient_data",
            "measured_on": None,
            "races_evaluated": 0,
            "samples": simulation_count,
            "targets": {},
            "note": (f"only {len(races)} completed race(s) recorded — at least "
                     f"{MIN_RACES_FOR_MEASUREMENT} are needed before reporting an accuracy figure"),
        }
        return result

    counts = {"winner": [0, 0], "podium": [0, 0], "points": [0, 0]}
    evaluated = 0
    for race_id, round_no in races:
        actual = _actual_for_round(round_no)
        if not actual:
            continue
        predicted = _score_race(race_id, simulation_count)
        if not predicted:
            continue
        evaluated += 1

        actual_winner = actual.get("winner")
        actual_podium = list(actual.get("podium", []))
        actual_points = list(actual.get("podium", []))  # recorded top-3 only

        if actual_winner and predicted["winner"]:
            counts["winner"][1] += 1
            counts["winner"][0] += int(predicted["winner"] == actual_winner)

        if actual_podium:
            counts["podium"][1] += 1
            predicted_top3 = set(predicted["podium"])
            # A podium hit = at least one of the predicted top 3 actually made it.
            # (Exact-order matching is reported separately by /predictions/history.)
            counts["podium"][0] += int(len(predicted_top3 & set(actual_podium)) > 0)

        if actual_points:
            counts["points"][1] += 1
            predicted_top10 = set(predicted["points"])
            counts["points"][0] += int(len(predicted_top10 & set(actual_points)) > 0)

    targets = {
        name: {
            "accuracy": (correct / total) if total else None,
            "correct": correct,
            "evaluated_races": total,
        }
        for name, (correct, total) in counts.items()
    }

    result = {
        "status": "measured" if evaluated else "insufficient_data",
        "measured_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "races_evaluated": evaluated,
        "samples": simulation_count,
        "targets": targets,
        "note": (
            "hit-rate measured by running the production predictor against each "
            "recorded race classification; podium/points count any overlap with "
            "the recorded top 3"
            if evaluated else
            "no race produced a scorable prediction"
        ),
    }

    with _CACHE_LOCK:
        _CACHE[cache_key] = (time.time(), result)
    return result
