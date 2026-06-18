"""
OpenF1 API Client — Live telemetry, timing, and race data.

Wraps the OpenF1 API (https://openf1.org/) to provide:
  - Car telemetry (speed, throttle, brake, RPM, gear, DRS) at 3.7 Hz
  - Real-time race positions and intervals
  - Lap times and sector times
  - Pit stop data and tire compounds
  - Weather conditions (track temp, air temp, humidity, wind, rain)
  - Race control events (flags, safety car, incidents)
  - Team radio transcripts
  - Session and meeting metadata

No API key required. Free tier: 3 req/s, 30 req/min.
Historical data available from 2023 season onwards.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from data.api_client import BaseAPIClient
from config.api_settings import (
    OPENF1_BASE_URL,
    OPENF1_RATE_LIMIT_RPS,
    OPENF1_RATE_LIMIT_RPM,
    OPENF1_TIMEOUT,
    OPENF1_ENABLED,
    CACHE_DIR,
    CACHE_TTL_SECONDS,
    CACHE_TTL_HISTORICAL_SECONDS,
    DRIVER_ID_TO_OPENF1_NUMBER,
)

logger = logging.getLogger(__name__)


class OpenF1Client(BaseAPIClient):
    """
    Client for the OpenF1 API.
    
    Provides structured access to all 18 OpenF1 endpoints with
    automatic caching, rate limiting, and error handling.
    """

    def __init__(self, enabled: bool = OPENF1_ENABLED):
        super().__init__(
            name="OpenF1",
            base_url=OPENF1_BASE_URL,
            rate_limit_rps=OPENF1_RATE_LIMIT_RPS,
            rate_limit_rpm=OPENF1_RATE_LIMIT_RPM,
            timeout=OPENF1_TIMEOUT,
            cache_dir=CACHE_DIR / "openf1",
            cache_enabled=True,
        )
        self.enabled = enabled

    # ── Session & Meeting Discovery ────────────────────────────────────────

    def get_meetings(self, year: Optional[int] = None) -> List[Dict]:
        """
        Get all race weekend meetings.
        
        Args:
            year: Filter by season year (e.g., 2025)
        
        Returns:
            List of meeting dicts with keys:
            - meeting_key, meeting_name, country_key, country_name,
              circuit_key, circuit_short_name, date_start, year
        """
        if not self.enabled:
            return []

        params = {}
        if year:
            params["year"] = year

        data = self.get("/meetings", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    def get_sessions(
        self,
        meeting_key: Optional[int] = None,
        year: Optional[int] = None,
        session_name: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get all sessions (P1, P2, P3, Qualifying, Sprint, Race).
        
        Args:
            meeting_key: Filter by meeting
            year: Filter by season year
            session_name: Filter by name (e.g., "Race", "Qualifying")
        
        Returns:
            List of session dicts with keys:
            - session_key, session_name, session_type, meeting_key,
              date_start, date_end, country_name, circuit_short_name
        """
        if not self.enabled:
            return []

        params = {}
        if meeting_key is not None:
            params["meeting_key"] = meeting_key
        if year:
            params["year"] = year
        if session_name:
            params["session_name"] = session_name

        data = self.get("/sessions", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    def find_race_session(self, year: int, meeting_name: str) -> Optional[Dict]:
        """
        Find the Race session for a specific meeting.
        
        Args:
            year: Season year
            meeting_name: Meeting name (partial match, e.g., "Monaco")
        
        Returns:
            Session dict for the Race, or None if not found
        """
        meetings = self.get_meetings(year=year)
        meeting = None
        for m in meetings:
            if meeting_name.lower() in m.get("meeting_name", "").lower():
                meeting = m
                break

        if not meeting:
            logger.warning(f"Meeting not found: {year} {meeting_name}")
            return None

        sessions = self.get_sessions(meeting_key=meeting["meeting_key"], session_name="Race")
        if sessions:
            return sessions[0]

        logger.warning(f"Race session not found for meeting {meeting['meeting_name']}")
        return None

    # ── Car Telemetry ──────────────────────────────────────────────────────

    def get_car_data(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        speed_gt: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get car telemetry data at 3.7 Hz sampling rate.
        
        Args:
            session_key: Session identifier
            driver_number: Filter by driver number
            speed_gt: Filter for data points where speed > value
        
        Returns:
            List of telemetry dicts with keys:
            - date, driver_number, speed, throttle, brake, RPM, gear, nGear,
              drs, session_key, meeting_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if speed_gt is not None:
            params["speed>"] = speed_gt

        data = self.get("/car_data", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    def get_driver_telemetry_summary(
        self,
        session_key: int,
        driver_number: int,
    ) -> Dict[str, Any]:
        """
        Get a summary of a driver's telemetry for a session.
        
        Computes aggregate metrics from raw telemetry:
        - Average/max speed, average throttle, brake events count
        - Average RPM, most-used gear
        - DRS usage count
        
        Args:
            session_key: Session identifier
            driver_number: Driver number
        
        Returns:
            Dict with summary metrics
        """
        car_data = self.get_car_data(session_key, driver_number=driver_number)

        if not car_data:
            return {"driver_number": driver_number, "error": "No telemetry data"}

        speeds = [d["speed"] for d in car_data if d.get("speed") is not None]
        throttles = [d["throttle"] for d in car_data if d.get("throttle") is not None]
        rpms = [d.get("RPM") or d.get("rpm") for d in car_data if d.get("RPM") or d.get("rpm") is not None]
        brakes = [d for d in car_data if d.get("brake") == 1]
        drs_events = [d for d in car_data if d.get("drs") and d["drs"] > 0]
        gears = [d.get("nGear") or d.get("gear") for d in car_data if d.get("nGear") is not None or d.get("gear") is not None]

        return {
            "driver_number": driver_number,
            "session_key": session_key,
            "data_points": len(car_data),
            "avg_speed": round(sum(speeds) / len(speeds), 1) if speeds else None,
            "max_speed": max(speeds) if speeds else None,
            "avg_throttle": round(sum(throttles) / len(throttles), 1) if throttles else None,
            "brake_events": len(brakes),
            "avg_rpm": round(sum(rpms) / len(rpms), 0) if rpms else None,
            "drs_usage_count": len(drs_events),
            "most_common_gear": max(set(gears), key=gears.count) if gears else None,
        }

    # ── Lap Data ───────────────────────────────────────────────────────────

    def get_laps(
        self,
        session_key: int,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get lap timing data.
        
        Args:
            session_key: Session identifier
            driver_number: Filter by driver
            lap_number: Filter by lap number
        
        Returns:
            List of lap dicts with keys:
            - date_start, lap_duration, lap_number, driver_number,
              segment_1_duration, segment_2_duration, segment_3_duration,
              is_pit_out_lap, stint_number, compound
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number
        if lap_number is not None:
            params["lap_number"] = lap_number

        data = self.get("/laps", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    def get_driver_lap_summary(self, session_key: int, driver_number: int) -> Dict[str, Any]:
        """
        Get a summary of a driver's lap performance in a session.
        
        Returns:
            Dict with: fastest_lap_time, avg_lap_time, total_laps,
            sector1_best, sector2_best, sector3_best
        """
        laps = self.get_laps(session_key, driver_number=driver_number)

        if not laps:
            return {"driver_number": driver_number, "error": "No lap data"}

        durations = [l["lap_duration"] for l in laps if l.get("lap_duration") is not None]
        s1 = [l["segment_1_duration"] for l in laps if l.get("segment_1_duration") is not None]
        s2 = [l["segment_2_duration"] for l in laps if l.get("segment_2_duration") is not None]
        s3 = [l["segment_3_duration"] for l in laps if l.get("segment_3_duration") is not None]

        return {
            "driver_number": driver_number,
            "session_key": session_key,
            "total_laps": len(laps),
            "fastest_lap_time": min(durations) if durations else None,
            "avg_lap_time": round(sum(durations) / len(durations), 3) if durations else None,
            "sector1_best": min(s1) if s1 else None,
            "sector2_best": min(s2) if s2 else None,
            "sector3_best": min(s3) if s3 else None,
        }

    # ── Positions & Intervals ──────────────────────────────────────────────

    def get_positions(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """
        Get real-time race positions (updated every 4 seconds during live).
        
        Returns:
            List of position dicts with keys:
            - date, driver_number, position, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number

        # Live data has shorter TTL
        ttl = CACHE_TTL_SECONDS if self._is_session_live(session_key) else CACHE_TTL_HISTORICAL_SECONDS
        data = self.get("/position", params=params, ttl_seconds=ttl)
        return data if isinstance(data, list) else []

    def get_intervals(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """
        Get gap-to-leader and interval-to-car-ahead data.
        
        Returns:
            List of interval dicts with keys:
            - date, driver_number, gap_to_leader, interval, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number

        ttl = CACHE_TTL_SECONDS if self._is_session_live(session_key) else CACHE_TTL_HISTORICAL_SECONDS
        data = self.get("/intervals", params=params, ttl_seconds=ttl)
        return data if isinstance(data, list) else []

    # ── Pit Stops ──────────────────────────────────────────────────────────

    def get_pit_stops(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """
        Get pit stop timing data.
        
        Returns:
            List of pit stop dicts with keys:
            - date, driver_number, lap_number, pit_duration, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number

        data = self.get("/pit", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    # ── Weather ────────────────────────────────────────────────────────────

    def get_weather(self, session_key: int) -> List[Dict]:
        """
        Get weather data for a session.
        
        Returns:
            List of weather dicts with keys:
            - date, air_temperature, humidity, pressure, rainfall,
              track_temperature, wind_speed, wind_direction, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        ttl = CACHE_TTL_SECONDS if self._is_session_live(session_key) else CACHE_TTL_HISTORICAL_SECONDS
        data = self.get("/weather", params=params, ttl_seconds=ttl)
        return data if isinstance(data, list) else []

    def get_weather_summary(self, session_key: int) -> Dict[str, Any]:
        """
        Get a weather summary for a session.
        
        Returns:
            Dict with: avg_air_temp, avg_track_temp, rained, humidity_avg,
            wind_speed_avg, rain_probability
        """
        weather = self.get_weather(session_key)

        if not weather:
            return {"session_key": session_key, "error": "No weather data"}

        air_temps = [w["air_temperature"] for w in weather if w.get("air_temperature") is not None]
        track_temps = [w["track_temperature"] for w in weather if w.get("track_temperature") is not None]
        humidities = [w["humidity"] for w in weather if w.get("humidity") is not None]
        winds = [w["wind_speed"] for w in weather if w.get("wind_speed") is not None]
        rain_events = [w for w in weather if w.get("rainfall")]

        return {
            "session_key": session_key,
            "data_points": len(weather),
            "avg_air_temp": round(sum(air_temps) / len(air_temps), 1) if air_temps else None,
            "avg_track_temp": round(sum(track_temps) / len(track_temps), 1) if track_temps else None,
            "avg_humidity": round(sum(humidities) / len(humidities), 1) if humidities else None,
            "avg_wind_speed": round(sum(winds) / len(winds), 1) if winds else None,
            "rained": len(rain_events) > 0,
            "rain_percentage": round(len(rain_events) / len(weather) * 100, 1) if weather else 0,
        }

    # ── Race Control ───────────────────────────────────────────────────────

    def get_race_control(self, session_key: int) -> List[Dict]:
        """
        Get race control events (flags, safety car, incidents, penalties).
        
        Returns:
            List of event dicts with keys:
            - date, category, flag, message, scope, sector,
              driver_number, lap_number, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        ttl = CACHE_TTL_SECONDS if self._is_session_live(session_key) else CACHE_TTL_HISTORICAL_SECONDS
        data = self.get("/race_control", params=params, ttl_seconds=ttl)
        return data if isinstance(data, list) else []

    def get_safety_car_summary(self, session_key: int) -> Dict[str, Any]:
        """
        Summarize safety car and flag events from race control data.
        
        Returns:
            Dict with: safety_car_deployments, red_flags, yellow_flags,
            penalties, total_incidents
        """
        events = self.get_race_control(session_key)

        if not events:
            return {"session_key": session_key, "error": "No race control data"}

        sc = [e for e in events if "safety car" in str(e.get("message", "")).lower()]
        red = [e for e in events if e.get("flag") == "RED"]
        yellow = [e for e in events if e.get("flag") == "YELLOW"]
        penalties = [e for e in events if e.get("category") == "Penalty"]

        return {
            "session_key": session_key,
            "safety_car_deployments": len(sc),
            "red_flags": len(red),
            "yellow_flags": len(yellow),
            "penalties": len(penalties),
            "total_incidents": len(events),
        }

    # ── Stints & Tires ─────────────────────────────────────────────────────

    def get_stints(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """
        Get tire stint data.
        
        Returns:
            List of stint dicts with keys:
            - driver_number, lap_start, lap_end, compound, stint_number,
              tyre_age_at_start, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number

        data = self.get("/stints", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    # ── Drivers ────────────────────────────────────────────────────────────

    def get_drivers(self, session_key: int) -> List[Dict]:
        """
        Get driver list for a session.
        
        Returns:
            List of driver dicts with keys:
            - driver_number, full_name, name_acronym, team_name,
              team_colour, first_name, last_name, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        data = self.get("/drivers", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    # ── Team Radio ─────────────────────────────────────────────────────────

    def get_team_radio(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """
        Get team radio recordings.
        
        Returns:
            List of radio dicts with keys:
            - date, driver_number, recording_url, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number

        data = self.get("/team_radio", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    # ── Location (Track Position) ──────────────────────────────────────────

    def get_location(self, session_key: int, driver_number: Optional[int] = None) -> List[Dict]:
        """
        Get car track position data (X, Y, Z coordinates).
        
        Returns:
            List of location dicts with keys:
            - date, driver_number, x, y, z, session_key
        """
        if not self.enabled:
            return []

        params = {"session_key": session_key}
        if driver_number is not None:
            params["driver_number"] = driver_number

        data = self.get("/location", params=params, ttl_seconds=CACHE_TTL_HISTORICAL_SECONDS)
        return data if isinstance(data, list) else []

    # ── Helper: Check if session is live ───────────────────────────────────

    def _is_session_live(self, session_key: int) -> bool:
        """
        Check if a session is currently live.
        
        Live = within 30 minutes before start to 30 minutes after end.
        """
        sessions = self.get_sessions()
        for s in sessions:
            if s.get("session_key") == session_key:
                try:
                    start = datetime.fromisoformat(s["date_start"].replace("Z", "+00:00"))
                    now = datetime.now(start.tzinfo) if start.tzinfo else datetime.now()
                    # Assume ~2 hour session duration + 30 min buffer
                    from datetime import timedelta
                    end = start + timedelta(hours=2, minutes=30)
                    buffer_start = start - timedelta(minutes=30)
                    buffer_end = end + timedelta(minutes=30)
                    return buffer_start <= now <= buffer_end
                except Exception:
                    pass
        return False

    # ── Convenience: Full Race Weekend Report ──────────────────────────────

    def get_race_weekend_report(self, year: int, meeting_name: str) -> Dict[str, Any]:
        """
        Get a comprehensive report for a race weekend.
        
        Combines data from multiple endpoints into a single report.
        
        Args:
            year: Season year
            meeting_name: Meeting name (partial match)
        
        Returns:
            Dict with: meeting_info, race_session, weather_summary,
            driver_list, safety_car_summary, fastest_laps
        """
        session = self.find_race_session(year, meeting_name)
        if not session:
            return {"error": f"Race session not found: {year} {meeting_name}"}

        session_key = session["session_key"]

        report = {
            "meeting_info": {
                "year": year,
                "meeting_name": session.get("meeting_name"),
                "circuit": session.get("circuit_short_name"),
                "country": session.get("country_name"),
                "date_start": session.get("date_start"),
            },
            "session_key": session_key,
            "weather_summary": self.get_weather_summary(session_key),
            "safety_car_summary": self.get_safety_car_summary(session_key),
        }

        # Get driver list
        drivers = self.get_drivers(session_key)
        report["driver_count"] = len(drivers)

        # Get fastest lap per driver
        fastest_laps = {}
        for driver in drivers:
            dnum = driver.get("driver_number")
            if dnum:
                lap_summary = self.get_driver_lap_summary(session_key, dnum)
                fastest_laps[driver.get("name_acronym", str(dnum))] = lap_summary
        report["driver_lap_summaries"] = fastest_laps

        return report


# ── Module-level singleton ────────────────────────────────────────────────────

_openf1_client: Optional[OpenF1Client] = None


def get_openf1_client() -> OpenF1Client:
    """Get or create the singleton OpenF1 client."""
    global _openf1_client
    if _openf1_client is None:
        _openf1_client = OpenF1Client()
    return _openf1_client


# ── EXPORT ────────────────────────────────────────────────────────────────────

__all__ = [
    "OpenF1Client",
    "get_openf1_client",
]
