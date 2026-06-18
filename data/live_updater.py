"""
Live Data Updater — Post-race auto-refresh pipeline.

Bridges external APIs (Jolpica, OpenF1) with the project's internal data layer:
  - Auto-updates driver standings and recent form from Jolpica
  - Auto-updates constructor strength ratings from live points
  - Syncs calendar race statuses from Jolpica schedule
  - Enriches FastF1 data with OpenF1 live supplements
  - Computes updated DNF rates from actual results
  - Generates data freshness reports

Designed to run after each race weekend to keep all hardcoded data fresh.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ── Driver Code ↔ Internal ID Mapping ─────────────────────────────────────────
# Maps Ergast/Jolpica driver codes to our internal driver IDs
_ERGAST_CODE_TO_OUR_ID = {
    "VER": "verstappen", "PER": "perez", "HAM": "hamilton",
    "LEC": "leclerc", "SAI": "sainz", "NOR": "norris",
    "PIA": "piastri", "ALO": "alonso", "STR": "stroll",
    "RUS": "russell", "ANT": "antonelli", "GAS": "gasly",
    "OCO": "ocon", "LAW": "lawson", "HAD": "hadjar",
    "LIN": "lindblad", "HUL": "hulkenberg", "BOR": "bortoleto",
    "ALB": "albon", "BEA": "bearman", "COL": "colapinto",
    "BOT": "bottas", "TSU": "tsunoda",
}

# Maps Ergast constructor names to our team IDs
_ERGAST_CONSTRUCTOR_TO_OUR_ID = {
    "mercedes": "mercedes", "ferrari": "ferrari",
    "red_bull": "red_bull", "mclaren": "mclaren",
    "williams": "williams", "alpine": "alpine",
    "haas": "haas", "aston_martin": "aston_martin",
    "audi": "audi", "rb": "rb", "cadillac": "cadillac",
}


class LiveUpdater:
    """
    Post-race data refresh pipeline.
    
    Uses Jolpica and OpenF1 clients to fetch live data and produce
    structured updates that can be applied to the project's data layer.
    """

    def __init__(self):
        from data.jolpica_client import get_jolpica_client
        from data.openf1_client import get_openf1_client

        self.jolpica = get_jolpica_client()
        self.openf1 = get_openf1_client()
        self._update_log: List[Dict[str, Any]] = []

    # ── 1. Driver Standings Update ─────────────────────────────────────────

    def fetch_driver_standings_update(self) -> Dict[str, Any]:
        """
        Fetch current driver standings from Jolpica and map to our IDs.
        
        Returns:
            Dict with:
            - standings: Dict[our_driver_id → {position, points, wins}]
            - timestamp: When data was fetched
            - source: "jolpica"
        """
        logger.info("Fetching driver standings from Jolpica...")

        mapped = self.jolpica.get_standings_mapped()

        if not mapped:
            logger.warning("No standings data returned from Jolpica")
            return {"standings": {}, "timestamp": datetime.now().isoformat(), "source": "jolpica", "error": "No data"}

        self._log_update("driver_standings", len(mapped))

        return {
            "standings": mapped,
            "timestamp": datetime.now().isoformat(),
            "source": "jolpica",
            "driver_count": len(mapped),
        }

    # ── 2. Constructor Standings Update ────────────────────────────────────

    def fetch_constructor_standings_update(self) -> Dict[str, Any]:
        """
        Fetch current constructor standings from Jolpica.
        
        Returns:
            Dict with:
            - standings: Dict[our_team_id → {position, points, wins}]
            - computed_strength: Dict[our_team_id → float 0-1] (normalized)
        """
        logger.info("Fetching constructor standings from Jolpica...")

        mapped = self.jolpica.get_constructor_standings_mapped()

        if not mapped:
            logger.warning("No constructor standings returned from Jolpica")
            return {"standings": {}, "computed_strength": {}, "timestamp": datetime.now().isoformat(), "source": "jolpica"}

        # Compute normalized constructor strength from points
        # Scale: max points → 0.96, min points → 0.10 (matching settings.py range)
        points_values = [v["points"] for v in mapped.values() if v["points"] > 0]
        if points_values:
            max_pts = max(points_values)
            min_pts = min(points_values)
            pts_range = max_pts - min_pts if max_pts != min_pts else 1

            computed_strength = {}
            for team_id, data in mapped.items():
                if data["points"] > 0:
                    normalized = (data["points"] - min_pts) / pts_range
                    computed_strength[team_id] = round(0.10 + normalized * 0.86, 2)
                else:
                    computed_strength[team_id] = 0.10
        else:
            computed_strength = {team_id: 0.50 for team_id in mapped}

        self._log_update("constructor_standings", len(mapped))

        return {
            "standings": mapped,
            "computed_strength": computed_strength,
            "timestamp": datetime.now().isoformat(),
            "source": "jolpica",
            "team_count": len(mapped),
        }

    # ── 3. Recent Race Results ─────────────────────────────────────────────

    def fetch_recent_results(self, num_races: int = 6) -> Dict[str, Any]:
        """
        Fetch recent race results from Jolpica.
        
        Args:
            num_races: Number of recent races to fetch
        
        Returns:
            Dict with:
            - races: List of race result dicts
            - driver_form: Dict[our_driver_id → List[int]] (recent finishing positions)
            - driver_dnf: Dict[our_driver_id → {starts, dnfs, dnf_rate}]
        """
        logger.info(f"Fetching last {num_races} race results from Jolpica...")

        # Get current schedule to find recent rounds
        schedule = self.jolpica.get_current_schedule()
        if not schedule:
            return {"races": [], "driver_form": {}, "driver_dnf": {}, "source": "jolpica"}

        # Find completed rounds (date <= today)
        today = datetime.now().date()
        completed = []
        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                if race_date <= today:
                    completed.append(race)
            except (ValueError, KeyError):
                continue

        # Take the last N completed races
        recent = completed[-num_races:] if len(completed) >= num_races else completed

        races = []
        driver_results: Dict[str, List[int]] = {}  # driver_id → [positions]
        driver_starts: Dict[str, int] = {}
        driver_dnfs: Dict[str, int] = {}

        for race in recent:
            round_num = race["round"]
            # Determine season from the schedule
            try:
                season = datetime.strptime(race["date"], "%Y-%m-%d").year
            except ValueError:
                season = datetime.now().year

            result = self.jolpica.get_race_results(season, round_num)
            if result and result.get("results"):
                races.append(result)

                for r in result["results"]:
                    # Map Ergast driver code to our ID
                    code = r.get("driver_code", "")
                    our_id = _ERGAST_CODE_TO_OUR_ID.get(code, code.lower())

                    pos = r.get("position", 0)
                    status = r.get("status", "")

                    # Track finishing positions
                    if pos > 0:
                        driver_results.setdefault(our_id, []).append(pos)

                    # Track starts and DNFs
                    driver_starts[our_id] = driver_starts.get(our_id, 0) + 1
                    if "finished" not in status.lower() and pos == 0:
                        driver_dnfs[our_id] = driver_dnfs.get(our_id, 0) + 1

        # Build recent form (last 6 results, most recent last)
        driver_form = {}
        for driver_id, positions in driver_results.items():
            driver_form[driver_id] = positions[-num_races:]

        # Build DNF rates
        driver_dnf = {}
        for driver_id, starts in driver_starts.items():
            dnfs = driver_dnfs.get(driver_id, 0)
            driver_dnf[driver_id] = {
                "starts": starts,
                "dnfs": dnfs,
                "dnf_rate": round(dnfs / starts, 3) if starts > 0 else 0.0,
            }

        self._log_update("recent_results", len(races))

        return {
            "races": races,
            "driver_form": driver_form,
            "driver_dnf": driver_dnf,
            "timestamp": datetime.now().isoformat(),
            "source": "jolpica",
            "race_count": len(races),
        }

    # ── 4. Calendar Status Sync ────────────────────────────────────────────

    def fetch_calendar_sync(self) -> Dict[str, Any]:
        """
        Sync calendar status from Jolpica schedule.
        
        Returns:
            Dict with:
            - races: List of {round, circuit, date, status}
            - next_race: Dict with info about the next upcoming race
        """
        logger.info("Syncing calendar from Jolpica...")

        schedule = self.jolpica.get_current_schedule()
        if not schedule:
            return {"races": [], "next_race": None, "source": "jolpica"}

        today = datetime.now().date()
        races = []
        next_race = None

        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                status = "completed" if race_date <= today else "upcoming"
            except (ValueError, KeyError):
                status = "tbc"
                race_date = None

            race_info = {
                "round": race["round"],
                "race_name": race["race_name"],
                "circuit_id": race.get("circuit_id", ""),
                "date": race.get("date", ""),
                "status": status,
            }
            races.append(race_info)

            # Find next upcoming race
            if status == "upcoming" and next_race is None:
                next_race = race_info

        self._log_update("calendar_sync", len(races))

        return {
            "races": races,
            "next_race": next_race,
            "completed_count": sum(1 for r in races if r["status"] == "completed"),
            "upcoming_count": sum(1 for r in races if r["status"] == "upcoming"),
            "timestamp": datetime.now().isoformat(),
            "source": "jolpica",
        }

    # ── 5. OpenF1 Race Weekend Supplement ──────────────────────────────────

    def fetch_race_weekend_supplement(self, year: int, meeting_name: str) -> Dict[str, Any]:
        """
        Fetch supplementary data from OpenF1 for a specific race weekend.
        
        Combines weather, safety car, and telemetry summaries.
        
        Args:
            year: Season year
            meeting_name: Meeting name (e.g., "Monaco")
        
        Returns:
            Dict with: weather, safety_car, driver_telemetry_summaries
        """
        logger.info(f"Fetching OpenF1 supplement for {year} {meeting_name}...")

        report = self.openf1.get_race_weekend_report(year, meeting_name)

        if "error" in report:
            logger.warning(f"OpenF1 supplement failed: {report['error']}")
            return {"error": report["error"], "source": "openf1"}

        self._log_update("openf1_supplement", 1)

        return {
            "meeting_info": report.get("meeting_info", {}),
            "weather_summary": report.get("weather_summary", {}),
            "safety_car_summary": report.get("safety_car_summary", {}),
            "driver_lap_summaries": report.get("driver_lap_summaries", {}),
            "timestamp": datetime.now().isoformat(),
            "source": "openf1",
        }

    # ── 6. Full Update Pipeline ────────────────────────────────────────────

    def run_full_update(self, include_openf1: bool = False) -> Dict[str, Any]:
        """
        Run the complete data update pipeline.
        
        Fetches fresh data from all sources and produces a unified update report.
        
        Args:
            include_openf1: Whether to also fetch OpenF1 supplement data
        
        Returns:
            Dict with all update results:
            - driver_standings: Updated standings
            - constructor_standings: Updated constructor standings + strength
            - recent_results: Recent race results + driver form + DNF rates
            - calendar: Synced calendar status
            - api_stats: Client usage statistics
            - update_log: Timestamped log of all updates performed
        """
        logger.info("=" * 60)
        logger.info("RUNNING FULL DATA UPDATE PIPELINE")
        logger.info("=" * 60)

        self._update_log = []
        start_time = datetime.now()

        # 1. Driver standings
        driver_standings = self.fetch_driver_standings_update()

        # 2. Constructor standings
        constructor_standings = self.fetch_constructor_standings_update()

        # 3. Recent results + form + DNF
        recent_results = self.fetch_recent_results(num_races=6)

        # 4. Calendar sync
        calendar = self.fetch_calendar_sync()

        # 5. Optional: OpenF1 supplement for the last completed race
        openf1_supplement = {}
        if include_openf1 and calendar.get("races"):
            completed = [r for r in calendar["races"] if r["status"] == "completed"]
            if completed:
                last_race = completed[-1]
                year = datetime.now().year
                openf1_supplement = self.fetch_race_weekend_supplement(
                    year, last_race["race_name"]
                )

        # Compile report
        elapsed = (datetime.now() - start_time).total_seconds()

        report = {
            "driver_standings": driver_standings,
            "constructor_standings": constructor_standings,
            "recent_results": recent_results,
            "calendar": calendar,
            "openf1_supplement": openf1_supplement,
            "api_stats": {
                "jolpica": self.jolpica.get_stats(),
                "openf1": self.openf1.get_stats(),
            },
            "update_log": self._update_log,
            "elapsed_seconds": round(elapsed, 2),
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }

        logger.info(f"Full update completed in {elapsed:.2f}s")
        logger.info(f"  Driver standings: {driver_standings.get('driver_count', 0)} drivers")
        logger.info(f"  Constructor standings: {constructor_standings.get('team_count', 0)} teams")
        logger.info(f"  Recent results: {recent_results.get('race_count', 0)} races")
        logger.info(f"  Calendar: {calendar.get('completed_count', 0)} completed, {calendar.get('upcoming_count', 0)} upcoming")
        logger.info("=" * 60)

        return report

    # ── 7. Generate Code Snippet for Hardcoded Data Update ─────────────────

    def generate_driver_data_patch(self) -> str:
        """
        Generate a Python code snippet showing what fields in driver_data.py
        should be updated based on fresh API data.
        
        Returns:
            String containing the suggested code changes
        """
        standings = self.fetch_driver_standings_update()
        recent = self.fetch_recent_results(num_races=6)

        if not standings.get("standings") or not recent.get("driver_form"):
            return "# No data available to generate patch"

        lines = [
            "# ── AUTO-GENERATED DRIVER DATA PATCH ──",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Source: Jolpica-F1 API",
            "",
            "# Update these fields in data/driver_data.py DRIVERS dict:",
            "",
        ]

        for driver_id, data in sorted(standings["standings"].items()):
            form = recent["driver_form"].get(driver_id, [])
            dnf_info = recent["driver_dnf"].get(driver_id, {})

            lines.append(f'    # {driver_id}:')
            lines.append(f'    #   "championship_points_2026": {int(data["points"])},')
            lines.append(f'    #   "wins_2026": {int(data["wins"])},')
            if form:
                lines.append(f'    #   "recent_form": {form},')
            if dnf_info:
                lines.append(f'    #   "dnf_rate_recent": {dnf_info.get("dnf_rate", 0.0)},')
            lines.append("")

        return "\n".join(lines)

    def generate_constructor_strength_patch(self) -> str:
        """
        Generate updated CONSTRUCTOR_STRENGTH values for settings.py.
        
        Returns:
            String containing the suggested code changes
        """
        update = self.fetch_constructor_standings_update()

        if not update.get("computed_strength"):
            return "# No data available to generate patch"

        lines = [
            "# ── AUTO-GENERATED CONSTRUCTOR STRENGTH PATCH ──",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Source: Jolpica-F1 API (computed from championship points)",
            "",
            "# Update CONSTRUCTOR_STRENGTH in config/settings.py:",
            "",
            "CONSTRUCTOR_STRENGTH = {",
        ]

        for team_id, strength in sorted(update["computed_strength"].items()):
            lines.append(f'    "{team_id}": {strength:.2f},')

        lines.append("}")
        return "\n".join(lines)

    # ── Internal ───────────────────────────────────────────────────────────

    def _log_update(self, update_type: str, count: int):
        """Log an update event."""
        entry = {
            "type": update_type,
            "count": count,
            "timestamp": datetime.now().isoformat(),
        }
        self._update_log.append(entry)
        logger.info(f"  ✓ {update_type}: {count} items updated")


# ── Module-level convenience function ─────────────────────────────────────────

_updater: Optional[LiveUpdater] = None


def get_live_updater() -> LiveUpdater:
    """Get or create the singleton LiveUpdater."""
    global _updater
    if _updater is None:
        _updater = LiveUpdater()
    return _updater


def run_full_data_update(include_openf1: bool = False) -> Dict[str, Any]:
    """
    Convenience function to run the full data update pipeline.
    
    This is the main entry point for refreshing all data after a race weekend.
    
    Args:
        include_openf1: Whether to also fetch OpenF1 supplement data
    
    Returns:
        Full update report dict
    """
    updater = get_live_updater()
    return updater.run_full_update(include_openf1=include_openf1)


# ── EXPORT ────────────────────────────────────────────────────────────────────

__all__ = [
    "LiveUpdater",
    "get_live_updater",
    "run_full_data_update",
]
