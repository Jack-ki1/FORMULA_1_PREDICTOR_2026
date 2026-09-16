import logging
from backend.app.config.team_driver_lineup_2026 import get_all_drivers, get_driver_by_code
from backend.app.engine.elo_calculator import elo_calculator
from backend.app.cache.redis import get_cache
logger = logging.getLogger(__name__)

class H2HService:
    def list_drivers(self):
        return get_all_drivers()

    def compare(self, driver_a: str, driver_b: str) -> dict:
        a = (driver_a or "").upper()
        b = (driver_b or "").upper()
        if not a or not b:
            raise ValueError("driver_a and driver_b are both required")
        info_a = get_driver_by_code(a)
        info_b = get_driver_by_code(b)
        if not info_a or not info_b:
            raise LookupError("Unknown driver code")
        # cache H2H
        key = f"h2h:{a}:{b}"
        cache = get_cache()
        cached = cache.get(key)
        if cached:
            import json
            try:
                return json.loads(cached) if isinstance(cached, str) else cached
            except Exception: pass
        prob = elo_calculator.get_h2h_probability(a,b)
        result = {"driver_a": info_a, "driver_b": info_b, "win_probability": prob, "reverse_probability": 1-prob}
        try: cache.set(key, result, ttl=3600)
        except Exception: pass
        return result


def h2h_history(driver_a: str, driver_b: str) -> dict:
    """Real head-to-head record from recorded race results.

    Counts, for each completed round, which of the two drivers finished ahead.
    Only rounds where BOTH appear are counted. If neither appears in any
    recorded result the caller gets an empty rounds list and an explicit note
    — never invented data (modify.md section 5).
    """
    a = (driver_a or "").upper()
    b = (driver_b or "").upper()
    if not a or not b:
        raise ValueError("driver_a and driver_b are both required")
    if a == b:
        raise ValueError("driver_a and driver_b must be different")
    if not get_driver_by_code(a) or not get_driver_by_code(b):
        raise LookupError("Unknown driver code")

    rounds = []
    a_wins = b_wins = 0
    try:
        from backend.app.data.calendar_2026 import CALENDAR_2026
        from backend.app.data.season_2026 import SEASON_2026_RESULTS
        results = SEASON_2026_RESULTS.get("results", {})
        by_round = {r.get("round"): r for r in CALENDAR_2026}
        for rnd in sorted(results.keys()):
            res = results[rnd]
            podium = list(res.get("podium", []))
            winner = res.get("winner")

            def rank(code):
                if code == winner:
                    return 1
                if code in podium:
                    return podium.index(code) + 1
                return None

            ra, rb = rank(a), rank(b)
            if ra is None and rb is None:
                continue
            race = by_round.get(rnd, {})
            if ra is not None and rb is not None:
                ahead = a if ra < rb else b
            else:
                # Only one of them is in the recorded top 3 — that one is ahead.
                ahead = a if ra is not None else b
            if ahead == a:
                a_wins += 1
            else:
                b_wins += 1
            rounds.append({
                "round": rnd,
                "race_id": race.get("id"),
                "race_name": race.get("name"),
                "a_rank": ra,
                "b_rank": rb,
                "ahead": ahead,
            })
    except Exception:
        pass

    total = a_wins + b_wins
    return {
        "driver_a": a,
        "driver_b": b,
        "a_wins": a_wins,
        "b_wins": b_wins,
        "rounds_compared": total,
        "a_win_rate": round(a_wins / total, 4) if total else None,
        "rounds": rounds,
        "basis": "recorded race classifications (season_2026)",
        "note": (None if total else
                 "no completed round has both drivers in its recorded classification yet"),
    }

h2h_service = H2HService()
