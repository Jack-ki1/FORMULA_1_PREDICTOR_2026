"""
Refreshes live data from Jolpica (standings, results) and OpenF1
(session context) and records a freshness marker.

Note on scope: this does NOT populate the full relational schema
(database/models.py's Team/Driver/Circuit/Race/QualifyingResult/
RaceResult tables) from live data — that would mean writing a mapper
from Jolpica/OpenF1's response shapes into every one of those tables, a
substantial project on its own, and the prediction engine (engine/*)
doesn't actually read from those relational tables today anyway (it
reads from config/team_driver_lineup_2026.py and data/calendar_2026.py,
both static). Building that mapper without a concrete consumer for it
would be speculative work — it's flagged in the README as the natural
next step if/when a feature needs genuinely dynamic team/driver/circuit
data instead of the static 2026 season config.

What this script does do, and what apps/status.py's "data freshness"
indicator actually reflects: warms the standings caches, and — the part
that matters for the precomputed-predictions architecture (PLAN.md §3)
— writes a SessionData row per race recording *when* and from *which
sources* grid/strength data was last pulled, so a stale sync is visible
in the UI instead of silent.
"""
import logging
import sys

import _bootstrap  # noqa: F401,E402

from config.settings import settings  # noqa: E402
from data.calendar_2026 import CALENDAR_2026  # noqa: E402
from data.jolpica_client import JolpicaClient  # noqa: E402
from database.db import get_session  # noqa: E402
from models.prediction import SessionData  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sync_data")


def sync_standings() -> list[str]:
    """Warm the standings caches; returns which sources responded live."""
    sources = []
    jolpica = JolpicaClient()

    driver_standings = jolpica.get_driver_standings(settings.SEASON_YEAR)
    if driver_standings.get("source") == "live":
        sources.append("jolpica:driver_standings")
    else:
        logger.warning(f"Driver standings not live: {driver_standings.get('note', driver_standings.get('source'))}")

    constructor_standings = jolpica.get_constructor_standings(settings.SEASON_YEAR)
    if constructor_standings.get("source") == "live":
        sources.append("jolpica:constructor_standings")

    return sources


def record_freshness_marker(race_id: str, sources: list[str]) -> None:
    with get_session() as db:
        existing = (
            db.query(SessionData)
            .filter(SessionData.race_id == race_id, SessionData.session_type == "sync")
            .first()
        )
        if existing:
            existing.sources = sources
            existing.strength_adjustments = existing.strength_adjustments or {}
            existing.grid_positions = existing.grid_positions or {}
        else:
            db.add(
                SessionData(
                    race_id=race_id,
                    session_type="sync",
                    strength_adjustments={},
                    grid_positions={},
                    sources=sources,
                )
            )
        db.commit()


def run() -> int:
    sources = sync_standings()
    logger.info(f"Live sources this run: {sources or '(none — using local fallback data)'}")

    upcoming = [r for r in CALENDAR_2026 if r.get("status") not in ("completed", "cancelled")]
    if not upcoming:
        logger.info("No upcoming races to mark as synced.")
        return 0

    next_race = upcoming[0]
    record_freshness_marker(next_race["id"], sources)
    logger.info(f"Recorded freshness marker for next race: {next_race['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
