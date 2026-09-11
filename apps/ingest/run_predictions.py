"""
Precomputes predictions for every upcoming race/session and persists
them to Postgres — this is what makes `GET /api/predictions/{race_id}`
a fast read in production instead of a multi-second Monte Carlo run on
every page load (see PLAN.md §3).

Run by .github/workflows/ingest-schedule.yml on a schedule. Can also be
run manually:

    cd apps/ingest && DATABASE_URL=... python run_predictions.py
    DATABASE_URL=... python run_predictions.py --race-id nl --only-race
"""
import argparse
import logging
import sys

import _bootstrap  # noqa: F401,E402

from data.calendar_2026 import CALENDAR_2026  # noqa: E402
from engine.predictor import generate_prediction  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("run_predictions")


def races_to_process(only_race_id: str | None) -> list[dict]:
    races = [r for r in CALENDAR_2026 if r.get("status") != "cancelled"]
    if only_race_id:
        races = [r for r in races if r["id"] == only_race_id]
    else:
        # Steady state: only bother precomputing races that haven't
        # happened yet. Completed races' predictions are historical and
        # don't need refreshing.
        races = [r for r in races if r.get("status") != "completed"]
    return races


def run(only_race_id: str | None, sessions: list[str], simulation_count: int) -> int:
    races = races_to_process(only_race_id)
    logger.info(f"Precomputing predictions for {len(races)} race(s), sessions={sessions}")

    failures = 0
    for race in races:
        for session_type in sessions:
            try:
                result = generate_prediction(
                    race_id=race["id"],
                    session_type=session_type,
                    simulation_count=simulation_count,
                )
                if result.get("status") == "success":
                    logger.info(f"  {race['id']} / {session_type}: ok")
                else:
                    logger.warning(f"  {race['id']} / {session_type}: {result}")
            except Exception as e:
                failures += 1
                logger.error(f"  {race['id']} / {session_type}: FAILED — {e}")

    logger.info(f"Done. {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--race-id", default=None, help="Only precompute this race (default: all upcoming)")
    parser.add_argument("--sessions", default="race,qualifying", help="Comma-separated session types")
    parser.add_argument("--simulation-count", type=int, default=10000)
    args = parser.parse_args()

    sys.exit(run(args.race_id, args.sessions.split(","), args.simulation_count))
