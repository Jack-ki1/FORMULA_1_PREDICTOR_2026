"""
Jolpica-F1 API Client — Historical results, standings, and schedules.

Wraps the Jolpica-F1 API (http://api.jolpi.ca/ergast/f1/) which provides
Ergast-compatible endpoints for:
  - Current and historical driver standings
  - Current and historical constructor standings
  - Race schedules and calendars
  - Race results, qualifying results, sprint results
  - Driver and constructor season results
  - Circuit information
  - Driver career information

No API key required. Free and open-source.
This is the modern replacement for the deprecated Ergast API.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from data.api_client import BaseAPIClient
from config.api_settings import (
    JOLPICA_BASE_URL,
    JOLPICA_RATE_LIMIT_RPS,
    JOLPICA_RATE_LIMIT_RPM,
    JOLPICA_TIMEOUT,
    JOLPICA_ENABLED,
    CACHE_DIR,
    CACHE_TTL_STANDINGS_SECONDS,
    CACHE_TTL_SCHEDULE_SECONDS,
    CACHE_TTL_HISTORICAL_SECONDS,
    DRIVER_ID_TO_JOLPICA,
    TEAM_ID_TO_JOLPICA,
)

logger = logging.getLogger(__name__)


class JolpicaClient(BaseAPIClient):
    """
    Client for the Jolpica-F1 API (Ergast-compatible endpoints).
    
    Provides structured access to historical F1 data including
    standings, results, schedules, and driver information.
    """

    def __init__(self, enabled: bool = JOLPICA_ENABLED):
        super().__init__(
            name="Jolpica",
            base_url=JOLPICA_BASE_URL,
            rate_limit_rps=JOLPICA_RATE_LIMIT_RPS,
            rate_limit_rpm=JOLPICA_RATE_LIMIT_RPM,
            timeout=JOLPICA_TIMEOUT,
            cache_dir=CACHE_DIR / "jolpica",
            cache_enabled=True,
        )
        self.enabled = enabled

    # ── Internal: Ergast response parser ───────────────────────────────────

    @staticmethod
    def _extract_mr_data(response: Any, table: str) -> List[Dict]:
        """
        Extract data from Ergast/Jolpica nested JSON response.
        
        Ergast responses have the structure:
        {
            "MRData": {
                "StandingsTable": {"StandingsLists": [...]},
                "RaceTable": {"Races": [...]},
                etc.
            }
        }
        """
        if not isinstance(response, dict):
            return []

        mr_data = response.get("MRData", {})
        table_data = mr_data.get(table, {})

        # Try common sub-keys
        for key in ["StandingsLists", "Races", "DriverTable", "ConstructorTable", "CircuitTable"]:
            items = table_data.get(key, [])
            if items:
                return items if isinstance(items, list) else [items]

        # Fallback: return the table data directly if it's a list
        if isinstance(table_data, list):
            return table_data

        return []

    # ── Championship Standings ─────────────────────────────────────────────

    def get_current_driver_standings(self) -> List[Dict[str, Any]]:
        """
        Get current season driver championship standings.
        
        Returns:
            List of driver standing dicts with keys:
            - position, position_text, points, wins, driver_id,
              driver_code, given_name, family_name, constructor, nationality
        """
        if not self.enabled:
            return []

        data = self.get("/current/driverStandings.json", ttl_seconds=CACHE_TTL_STANDINGS_SECONDS)
        if not data:
            return []

        standings_lists = self._extract_mr_data(data, "StandingsTable")
        if not standings_lists:
            return []

        # Get the most recent standings list
        latest = standings_lists[-1] if standings_lists else {}
        driver_list = latest.get("DriverStandings", [])

        result = []
        for entry in driver_list:
            driver = entry.get("Driver", {})
            constructors = entry.get("Constructors", [])
            constructor_name = constructors[0].get("name", "") if constructors else ""

            result.append({
                "position": int(entry.get("position", 0)),
                "position_text": entry.get("positionText", ""),
                "points": float(entry.get("points", 0)),
                "wins": int(entry.get("wins", 0)),
                "driver_id": driver.get("driverId", ""),
                "driver_code": driver.get("code", ""),
                "given_name": driver.get("givenName", ""),
                "family_name": driver.get("familyName", ""),
                "nationality": driver.get("nationality", ""),
                "constructor": constructor_name,
                "number": driver.get("permanentNumber", ""),
            })

        return result

    def get_current_constructor_standings(self) -> List[Dict[str, Any]]:
        """
        Get current season constructor championship standings.
        
        Returns:
            List of constructor standing dicts with keys:
            - position, points, wins, constructor_id, constructor_name, nationality
        """
        if not self.enabled:
            return []

        data = self.get("/current/constructorStandings.json", ttl_seconds=CACHE_TTL_STANDINGS_SECONDS)
        if not data:
            return []

        standings_lists = self._extract_mr_data(data, "StandingsTable")
        if not standings_lists:
            return []

        latest = standings_lists[-1] if standings_lists else {}
        constructor_list = latest.get("ConstructorStandings", [])

        result = []
        for entry in constructor_list:
            constructor = entry.get("Constructor", {})
            result.append({
                "position": int(entry.get("position", 0)),
                "points": float(entry.get("points", 0)),
                "wins": int(entry.get("wins", 0)),
                "constructor_id": constructor.get("constructorId", ""),
                "constructor_name": constructor.get("name", ""),
                "nationality": constructor.get("nationality", ""),
            })

        return result

    def get_driver_standings_at_round(self, season: int, round_num: int) -> List[Dict[str, Any]]:
        """
        Get driver standings after a specific round.
        
        Args:
            season: Year
            round_num: Round number
        
        Returns:
            List of driver standing dicts (same format as get_current_driver_standings)
        """
        if not self.enabled:
            return []

        endpoint = f"/{season}/{round_num}/driverStandings.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        if not data:
            return []

        standings_lists = self._extract_mr_data(data, "StandingsTable")
        if not standings_lists:
            return []

        latest = standings_lists[-1]
        driver_list = latest.get("DriverStandings", [])

        result = []
        for entry in driver_list:
            driver = entry.get("Driver", {})
            constructors = entry.get("Constructors", [])
            constructor_name = constructors[0].get("name", "") if constructors else ""

            result.append({
                "position": int(entry.get("position", 0)),
                "points": float(entry.get("points", 0)),
                "wins": int(entry.get("wins", 0)),
                "driver_id": driver.get("driverId", ""),
                "driver_code": driver.get("code", ""),
                "given_name": driver.get("givenName", ""),
                "family_name": driver.get("familyName", ""),
                "constructor": constructor_name,
            })

        return result

    # ── Schedule / Calendar ────────────────────────────────────────────────

    def get_current_schedule(self) -> List[Dict[str, Any]]:
        """
        Get current season race schedule.
        
        Returns:
            List of race dicts with keys:
            - round, race_name, circuit_id, circuit_name, locality, country,
              date, time, url
        """
        if not self.enabled:
            return []

        data = self.get("/current.json", ttl_seconds=CACHE_TTL_SCHEDULE_SECONDS)
        if not data:
            return []

        races = self._extract_mr_data(data, "RaceTable")
        if not races:
            return []

        # RaceTable contains a list with one element that has "Races" key
        race_list = races[0].get("Races", []) if races else []

        result = []
        for race in race_list:
            circuit = race.get("Circuit", {})
            location = circuit.get("Location", {})

            result.append({
                "round": int(race.get("round", 0)),
                "race_name": race.get("raceName", ""),
                "circuit_id": circuit.get("circuitId", ""),
                "circuit_name": circuit.get("circuitName", ""),
                "locality": location.get("locality", ""),
                "country": location.get("country", ""),
                "lat": float(location.get("lat", 0)),
                "lng": float(location.get("long", 0)),
                "date": race.get("date", ""),
                "time": race.get("time", ""),
                "url": race.get("url", ""),
            })

        return result

    def get_season_schedule(self, season: int) -> List[Dict[str, Any]]:
        """
        Get race schedule for a specific season.
        
        Args:
            season: Year (e.g., 2025)
        
        Returns:
            List of race dicts (same format as get_current_schedule)
        """
        if not self.enabled:
            return []

        endpoint = f"/{season}.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_SCHEDULE_SECONDS)
        if not data:
            return []

        races = self._extract_mr_data(data, "RaceTable")
        if not races:
            return []

        race_list = races[0].get("Races", []) if races else []

        result = []
        for race in race_list:
            circuit = race.get("Circuit", {})
            location = circuit.get("Location", {})

            result.append({
                "round": int(race.get("round", 0)),
                "race_name": race.get("raceName", ""),
                "circuit_id": circuit.get("circuitId", ""),
                "circuit_name": circuit.get("circuitName", ""),
                "locality": location.get("locality", ""),
                "country": location.get("country", ""),
                "date": race.get("date", ""),
                "time": race.get("time", ""),
            })

        return result

    # ── Race Results ───────────────────────────────────────────────────────

    def get_race_results(self, season: int, round_num: int) -> Dict[str, Any]:
        """
        Get race results for a specific race.
        
        Args:
            season: Year
            round_num: Round number
        
        Returns:
            Dict with: race_name, circuit, date, results (list of driver results)
        """
        if not self.enabled:
            return {}

        endpoint = f"/{season}/{round_num}/results.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        if not data:
            return {}

        races = self._extract_mr_data(data, "RaceTable")
        if not races:
            return {}

        race_list = races[0].get("Races", []) if races else []
        if not race_list:
            return {}

        race = race_list[0]
        circuit = race.get("Circuit", {})
        results_raw = race.get("Results", [])

        results = []
        for r in results_raw:
            driver = r.get("Driver", {})
            constructor = r.get("Constructor", {})
            time_info = r.get("Time", {})

            results.append({
                "position": int(r.get("position", 0)),
                "points": float(r.get("points", 0)),
                "driver_id": driver.get("driverId", ""),
                "driver_code": driver.get("code", ""),
                "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}",
                "constructor_id": constructor.get("constructorId", ""),
                "constructor_name": constructor.get("name", ""),
                "grid": int(r.get("grid", 0)),
                "laps": int(r.get("laps", 0)),
                "status": r.get("status", ""),
                "time": time_info.get("time", ""),
                "time_millis": time_info.get("millis", 0),
            })

        return {
            "season": season,
            "round": round_num,
            "race_name": race.get("raceName", ""),
            "circuit_id": circuit.get("circuitId", ""),
            "circuit_name": circuit.get("circuitName", ""),
            "date": race.get("date", ""),
            "results": results,
        }

    def get_qualifying_results(self, season: int, round_num: int) -> Dict[str, Any]:
        """
        Get qualifying results for a specific race.
        
        Returns:
            Dict with: race_name, circuit, date, qualifying_results
        """
        if not self.enabled:
            return {}

        endpoint = f"/{season}/{round_num}/qualifying.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        if not data:
            return {}

        races = self._extract_mr_data(data, "RaceTable")
        if not races:
            return {}

        race_list = races[0].get("Races", []) if races else []
        if not race_list:
            return {}

        race = race_list[0]
        qual_raw = race.get("QualifyingResults", [])

        results = []
        for r in qual_raw:
            driver = r.get("Driver", {})
            constructor = r.get("Constructor", {})

            results.append({
                "position": int(r.get("position", 0)),
                "driver_id": driver.get("driverId", ""),
                "driver_code": driver.get("code", ""),
                "constructor_id": constructor.get("constructorId", ""),
                "q1": r.get("Q1", ""),
                "q2": r.get("Q2", ""),
                "q3": r.get("Q3", ""),
            })

        return {
            "season": season,
            "round": round_num,
            "race_name": race.get("raceName", ""),
            "date": race.get("date", ""),
            "qualifying_results": results,
        }

    def get_sprint_results(self, season: int, round_num: int) -> Dict[str, Any]:
        """
        Get sprint race results for a specific race (sprint weekends only).
        
        Returns:
            Dict with: race_name, circuit, date, results (same format as race results)
        """
        if not self.enabled:
            return {}
        
        endpoint = f"/{season}/{round_num}/sprint.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        if not data:
            return {}
        
        races = self._extract_mr_data(data, "RaceTable")
        if not races:
            return {}
        
        race_list = races[0].get("Races", []) if races else []
        if not race_list:
            return {}
        
        race = race_list[0]
        circuit = race.get("Circuit", {})
        results_raw = race.get("Results", [])
        
        results = []
        for r in results_raw:
            driver = r.get("Driver", {})
            constructor = r.get("Constructor", {})
            time_info = r.get("Time", {})
            
            results.append({
                "position": int(r.get("position", 0)),
                "points": float(r.get("points", 0)),
                "driver_id": driver.get("driverId", ""),
                "driver_code": driver.get("code", ""),
                "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}",
                "constructor_id": constructor.get("constructorId", ""),
                "constructor_name": constructor.get("name", ""),
                "grid": int(r.get("grid", 0)),
                "laps": int(r.get("laps", 0)),
                "status": r.get("status", ""),
                "time": time_info.get("time", ""),
                "time_millis": time_info.get("millis", 0),
            })
        
        return {
            "season": season,
            "round": round_num,
            "race_name": race.get("raceName", ""),
            "circuit_id": circuit.get("circuitId", ""),
            "circuit_name": circuit.get("circuitName", ""),
            "date": race.get("date", ""),
            "results": results,
        }

    def get_session_results(self, season: int, round_num: int, session_type: str) -> Dict[str, Any]:
        """Fetch a race-weekend session using a stable session-type name."""
        key = (session_type or "").lower().replace(" ", "_")
        if key in {"race", "r", "grand_prix"}:
            return self.get_race_results(season, round_num)
        if key in {"qualifying", "qual", "q"}:
            return self.get_qualifying_results(season, round_num)
        if key in {"sprint", "sprint_race"}:
            return self.get_sprint_results(season, round_num)
        return {}

    def get_weekend_results(self, season: int, round_num: int) -> Dict[str, Any]:
        """Fetch all Jolpica-supported classifications for a weekend."""
        race = self.get_race_results(season, round_num)
        qualifying = self.get_qualifying_results(season, round_num)
        sprint = self.get_sprint_results(season, round_num)
        sessions = {}
        if qualifying.get("qualifying_results"):
            sessions["qualifying"] = qualifying
        if sprint.get("results"):
            sessions["sprint"] = sprint
        if race.get("results"):
            sessions["race"] = race
        return {
            "season": season,
            "round": round_num,
            "sessions": sessions,
            "session_count": len(sessions),
            "source": "jolpica",
        }

    @staticmethod
    def normalize_grid_to_internal_ids(results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Map Jolpica qualifying rows to internal driver IDs and grid positions."""
        reverse_map = {v: k for k, v in DRIVER_ID_TO_JOLPICA.items()}
        grid: Dict[str, int] = {}
        for result in results or []:
            external_id = result.get("driver_id", "")
            internal_id = reverse_map.get(external_id, external_id)
            position = result.get("position")
            if internal_id and position:
                grid[internal_id] = int(position)
        return grid

    def get_last_race_results(self) -> Dict[str, Any]:
        """
        Get the most recent completed race results.
        
        Returns:
            Dict with race results (same format as get_race_results)
        """
        if not self.enabled:
            return {}

        data = self.get("/current/last/results.json", ttl_seconds=CACHE_TTL_STANDINGS_SECONDS)
        if not data:
            return {}

        races = self._extract_mr_data(data, "RaceTable")
        if not races:
            return {}

        race_list = races[0].get("Races", []) if races else []
        if not race_list:
            return {}

        race = race_list[0]
        circuit = race.get("Circuit", {})
        results_raw = race.get("Results", [])

        results = []
        for r in results_raw:
            driver = r.get("Driver", {})
            constructor = r.get("Constructor", {})

            results.append({
                "position": int(r.get("position", 0)),
                "points": float(r.get("points", 0)),
                "driver_id": driver.get("driverId", ""),
                "driver_code": driver.get("code", ""),
                "constructor_id": constructor.get("constructorId", ""),
                "grid": int(r.get("grid", 0)),
                "laps": int(r.get("laps", 0)),
                "status": r.get("status", ""),
            })

        return {
            "season": int(race.get("season", 0)),
            "round": int(race.get("round", 0)),
            "race_name": race.get("raceName", ""),
            "circuit_id": circuit.get("circuitId", ""),
            "date": race.get("date", ""),
            "results": results,
        }

    # ── Season Results (All Races) ─────────────────────────────────────────

    def get_season_results(self, season: int) -> List[Dict[str, Any]]:
        """
        Get all race results for a season.
        
        Args:
            season: Year
        
        Returns:
            List of race result dicts
        """
        if not self.enabled:
            return []

        # First get the schedule to know how many rounds
        schedule = self.get_season_schedule(season)
        if not schedule:
            return []

        all_results = []
        for race in schedule:
            round_num = race["round"]
            result = self.get_race_results(season, round_num)
            if result:
                all_results.append(result)

        return all_results

    # ── Driver Info ────────────────────────────────────────────────────────

    def get_driver_info(self, driver_id: str) -> Dict[str, Any]:
        """
        Get information about a specific driver.
        
        Args:
            driver_id: Ergast-style driver ID (e.g., "max_verstappen")
        
        Returns:
            Dict with driver info: name, nationality, birthday, URL
        """
        if not self.enabled:
            return {}

        endpoint = f"/drivers/{driver_id}.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        if not data:
            return {}

        drivers = self._extract_mr_data(data, "DriverTable")
        if not drivers:
            return {}

        driver_list = drivers[0].get("Drivers", []) if drivers else []
        if not driver_list:
            return {}

        driver = driver_list[0]
        return {
            "driver_id": driver.get("driverId", ""),
            "permanent_number": driver.get("permanentNumber", ""),
            "code": driver.get("code", ""),
            "given_name": driver.get("givenName", ""),
            "family_name": driver.get("familyName", ""),
            "date_of_birth": driver.get("dateOfBirth", ""),
            "nationality": driver.get("nationality", ""),
            "url": driver.get("url", ""),
        }

    # ── Circuit Info ───────────────────────────────────────────────────────

    def get_circuit_info(self, circuit_id: str) -> Dict[str, Any]:
        """
        Get information about a specific circuit.
        
        Args:
            circuit_id: Ergast-style circuit ID (e.g., "monaco")
        
        Returns:
            Dict with circuit info: name, locality, country, coordinates, URL
        """
        if not self.enabled:
            return {}

        endpoint = f"/circuits/{circuit_id}.json"
        data = self.get(endpoint, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        if not data:
            return {}

        circuits = self._extract_mr_data(data, "CircuitTable")
        if not circuits:
            return {}

        circuit_list = circuits[0].get("Circuits", []) if circuits else []
        if not circuit_list:
            return {}

        circuit = circuit_list[0]
        location = circuit.get("Location", {})

        return {
            "circuit_id": circuit.get("circuitId", ""),
            "circuit_name": circuit.get("circuitName", ""),
            "locality": location.get("locality", ""),
            "country": location.get("country", ""),
            "lat": float(location.get("lat", 0)),
            "lng": float(location.get("long", 0)),
            "url": circuit.get("url", ""),
        }

    # ── Convenience: Map Jolpica standings → our driver IDs ────────────────

    def get_standings_mapped(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current driver standings mapped to our internal driver IDs.
        
        Returns:
            Dict keyed by our driver_id (e.g., "verstappen") with:
            - position, points, wins, constructor
        """
        standings = self.get_current_driver_standings()

        # Build reverse mapping: jolpica_id → our_id
        reverse_map = {v: k for k, v in DRIVER_ID_TO_JOLPICA.items()}

        mapped = {}
        for entry in standings:
            jolpica_id = entry.get("driver_id", "")
            our_id = reverse_map.get(jolpica_id, jolpica_id)
            mapped[our_id] = {
                "position": entry["position"],
                "points": entry["points"],
                "wins": entry["wins"],
                "constructor": entry.get("constructor", ""),
                "driver_code": entry.get("driver_code", ""),
            }

        return mapped

    def get_constructor_standings_mapped(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current constructor standings mapped to our internal team IDs.
        
        Returns:
            Dict keyed by our team_id (e.g., "red_bull") with:
            - position, points, wins
        """
        standings = self.get_current_constructor_standings()

        # Build reverse mapping: jolpica_id → our_id
        reverse_map = {v: k for k, v in TEAM_ID_TO_JOLPICA.items()}

        mapped = {}
        for entry in standings:
            jolpica_id = entry.get("constructor_id", "")
            our_id = reverse_map.get(jolpica_id, jolpica_id)
            mapped[our_id] = {
                "position": entry["position"],
                "points": entry["points"],
                "wins": entry["wins"],
            }

        return mapped


# ── Module-level singleton ────────────────────────────────────────────────────

_jolpica_client: Optional[JolpicaClient] = None


def get_jolpica_client() -> JolpicaClient:
    """Get or create the singleton Jolpica client."""
    global _jolpica_client
    if _jolpica_client is None:
        _jolpica_client = JolpicaClient()
    return _jolpica_client


# ── EXPORT ────────────────────────────────────────────────────────────────────

__all__ = [
    "JolpicaClient",
    "get_jolpica_client",
]
