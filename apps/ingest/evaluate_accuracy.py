"""
Post-race scoring for the fantasy league feature (PLAN.md §7).

For every completed race with pending picks, fetches the actual result
via JolpicaClient and scores each pick using the same point values as
`engine/fantasy_scoring.py`'s real F1-fantasy ruleset (not calling that
class directly — it's built around full per-driver race telemetry
(finishing position, overtakes, DNF flag, ...) we don't have here, but
its `scoring_rules` dict is the single source of truth for point values
either way, so this reuses that rather than hardcoding its own numbers).

Result parsing handles two shapes:
  - Live Jolpica/Ergast-style JSON (MRData.RaceTable.Races[0].Results[]).
    Written to the documented Ergast schema but not exercised against a
    live response in this environment (no network access to jolpica-f1
    from here) — if the live shape doesn't parse, this falls back
    gracefully to skipping the race rather than crashing, and logs a
    warning for a human to check.
  - The local fallback/simulated shape from data/season_2026.py
    (`{'winner': 'VER', 'podium': [...], 'fastest_lap': 'VER'}`), which
    is what's actually exercised by the test suite.
"""
import logging
import sys
from typing import Any

import _bootstrap  # noqa: F401,E402

from config.settings import settings  # noqa: E402
from data.calendar_2026 import CALENDAR_2026  # noqa: E402
from data.jolpica_client import JolpicaClient  # noqa: E402
from database.db import get_session  # noqa: E402
from database.models import UserPick, LeaderboardEntry  # noqa: E402
from engine.fantasy_scoring import FantasyScoring  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("evaluate_accuracy")

# Pole/fastest-lap picks are scored with a flat bonus rather than the
# (very small, by design, in the real F1-fantasy ruleset) 1-point
# fastest_lap_bonus — a 1-point swing doesn't feel meaningful in a
# pick-em leaderboard context. Position-based targets (winner/podium)
# use FantasyScoring's real position_points table unmodified.
POLE_BONUS = 10
FASTEST_LAP_BONUS = 10


def _extract_result(raw: dict) -> dict[str, Any] | None:
    """Normalize either the live Ergast-style shape or the local
    fallback shape into {'winner': code, 'podium': [codes], 'fastest_lap': code}."""
    data = raw.get("data")

    # Local fallback shape (data/season_2026.py) — already normalized.
    if isinstance(data, dict) and "winner" in data and "podium" in data:
        return {
            "winner": data["winner"],
            "podium": data["podium"],
            "fastest_lap": data.get("fastest_lap"),
        }

    # Live Ergast/Jolpica shape.
    try:
        races = raw["MRData"]["RaceTable"]["Races"]
        if not races:
            return None
        results = races[0]["Results"]
        podium = []
        fastest_lap_code = None
        for entry in sorted(results, key=lambda r: int(r["position"])):
            code = entry["Driver"].get("code") or entry["Driver"].get("driverId", "").upper()[:3]
            if int(entry["position"]) <= 3:
                podium.append(code)
            fl = entry.get("FastestLap")
            if fl and fl.get("rank") == "1":
                fastest_lap_code = code
        if not podium:
            return None
        return {"winner": podium[0], "podium": podium, "fastest_lap": fastest_lap_code}
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def _score_pick(pick: UserPick, result: dict[str, Any], scoring: FantasyScoring) -> int:
    position_points = scoring.scoring_rules["position_points"]

    if pick.target in ("winner", "podium"):
        if pick.driver_id in result["podium"]:
            position = result["podium"].index(pick.driver_id) + 1
            return position_points.get(position, 0)
        return 0

    if pick.target == "pole":
        # No qualifying data threaded through here yet (race results
        # only) — pole picks stay pending until a future run adds
        # qualifying-result fetching. Returning None signals "skip".
        return None  # type: ignore[return-value]

    if pick.target == "fastest_lap":
        return FASTEST_LAP_BONUS if pick.driver_id == result.get("fastest_lap") else 0

    return 0


def run() -> int:
    jolpica = JolpicaClient()
    completed = [r for r in CALENDAR_2026 if r.get("status") == "completed"]

    with get_session() as db:
        pending = db.query(UserPick).filter(UserPick.status == "pending").all()
        if not pending:
            logger.info("No pending picks to evaluate.")
            return 0

        pending_race_ids = {p.race_id for p in pending}
        scoring = FantasyScoring()
        resolved_count = 0

        for race in completed:
            if race["id"] not in pending_race_ids:
                continue

            raw = jolpica.get_race_result(settings.SEASON_YEAR, race["round"])
            result = _extract_result(raw)
            if result is None:
                logger.warning(f"Could not parse result for {race['id']} (round {race['round']}) — skipping")
                continue

            race_picks = [p for p in pending if p.race_id == race["id"] and p.session == "race"]
            for pick in race_picks:
                points = _score_pick(pick, result, scoring)
                if points is None:
                    continue  # pole picks, not yet scorable — stays pending
                pick.points = points
                pick.status = "resolved"
                resolved_count += 1

                entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.user_id == pick.user_id).first()
                if entry:
                    entry.total_score = (entry.total_score or 0) + points
                    entry.picks_resolved = (entry.picks_resolved or 0) + 1

            logger.info(f"{race['id']}: resolved {len(race_picks)} pick(s)")

        db.commit()

    logger.info(f"Done. {resolved_count} pick(s) resolved this run.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
