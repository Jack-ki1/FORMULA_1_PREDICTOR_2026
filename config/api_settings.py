"""
API Settings — Configuration for all external F1 data sources.

Manages endpoints, rate limits, API keys, caching, and feature flags for:
  - OpenF1 API (live telemetry, positions, race control)
  - Jolpica-F1 API (historical results, standings, schedules)
  - API-Sports F1 (optional — schedules, standings, results)
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
import json
import logging

logger = logging.getLogger(__name__)


# ── OpenF1 API Configuration ──────────────────────────────────────────────────

OPENF1_BASE_URL = "https://api.openf1.org/v1"
OPENF1_RATE_LIMIT_RPS = 3        # 3 requests per second (free tier)
OPENF1_RATE_LIMIT_RPM = 30       # 30 requests per minute (free tier)
OPENF1_TIMEOUT = 15              # seconds
OPENF1_ENABLED = os.environ.get("OPENF1_ENABLED", "true").lower() == "true"

# OpenF1 available endpoints (18 total)
OPENF1_ENDPOINTS = {
    "car_data":       "/car_data",        # Telemetry: speed, throttle, brake, RPM, gear, DRS
    "drivers":        "/drivers",         # Driver list for a session
    "intervals":      "/intervals",       # Gap to leader, interval to car ahead
    "laps":           "/laps",            # Lap times, sector times, compounds
    "location":       "/location",        # Car X/Y/Z track position
    "meetings":       "/meetings",        # Race weekend metadata
    "pit":            "/pit",             # Pit stop timing and duration
    "position":       "/position",        # Real-time race positions
    "race_control":   "/race_control",    # Flags, safety car, incidents
    "sessions":       "/sessions",        # Session metadata (P1, P2, Q, R)
    "stints":         "/stints",          # Tire stint data
    "team_radio":     "/team_radio",      # Driver-pit audio transcripts
    "weather":        "/weather",         # Track/air temp, humidity, wind, rain
    "circuits":       "/circuits",        # Circuit metadata
    "championship":   "/championship",    # Live driver/constructor standings  # NOTE: may not exist yet
}


# ── Jolpica-F1 API Configuration ─────────────────────────────────────────────

JOLPICA_BASE_URL = "http://api.jolpi.ca/ergast/f1"
JOLPICA_RATE_LIMIT_RPS = 4
JOLPICA_RATE_LIMIT_RPM = 60
JOLPICA_TIMEOUT = 20             # seconds
JOLPICA_ENABLED = os.environ.get("JOLPICA_ENABLED", "true").lower() == "true"

# Jolpica (Ergast-compatible) endpoints
JOLPICA_ENDPOINTS = {
    "current_driver_standings":  "/current/driverStandings.json",
    "current_constructor_standings": "/current/constructorStandings.json",
    "current_schedule":          "/current.json",
    "season_results":            "/{season}.json",            # All races for a season
    "race_results":              "/{season}/{round}/results.json",
    "qualifying_results":        "/{season}/{round}/qualifying.json",
    "sprint_results":            "/{season}/{round}/sprint.json",
    "driver_season":             "/{season}/drivers/{driver}/results.json",
    "constructor_season":        "/{season}/constructors/{constructor}/results.json",
    "circuit_info":              "/circuits/{circuit_id}.json",
    "driver_info":               "/drivers/{driver_id}.json",
    "season_driver_standings":   "/{season}/{round}/driverStandings.json",
    "season_constructor_standings": "/{season}/{round}/constructorStandings.json",
    "last_race_results":         "/current/last/results.json",
}


# ── API-Sports F1 Configuration (Optional) ────────────────────────────────────

APISPORTS_BASE_URL = "https://v1.formula-1.api-sports.io"
APISPORTS_API_KEY = os.environ.get("APISPORTS_F1_API_KEY", "")
APISPORTS_RATE_LIMIT_RPD = 100   # 100 requests per day (free tier)
APISPORTS_TIMEOUT = 15
APISPORTS_ENABLED = bool(APISPORTS_API_KEY)  # Only enable if key is set


# ── Caching Configuration ─────────────────────────────────────────────────────

# Local cache directory for API responses
CACHE_DIR = Path(__file__).resolve().parents[1] / "cache" / "api_responses"
CACHE_ENABLED = True
CACHE_TTL_SECONDS = 600          # 10 minutes for live data (increased to reduce API calls)
CACHE_TTL_LIVE_TIMING_SECONDS = 60  # Increased from 30s
CACHE_TTL_LIVE_WEATHER_SECONDS = 120  # Increased from 60s
CACHE_TTL_SESSION_RESULTS_SECONDS = 600
CACHE_TTL_STANDINGS_SECONDS = 3600  # 1 hour for standings (changes less often)
CACHE_TTL_SCHEDULE_SECONDS = 86400  # 24 hours for schedule (rarely changes)
CACHE_TTL_HISTORICAL_SECONDS = 604800  # 7 days for historical data


# ── Feature Flags ─────────────────────────────────────────────────────────────

# Enable/disable individual data source integrations
FEATURE_FLAGS = {
    "openf1_live_data":        OPENF1_ENABLED,
    "openf1_telemetry":        OPENF1_ENABLED,
    "openf1_weather":          OPENF1_ENABLED,
    "openf1_race_control":     OPENF1_ENABLED,
    "jolpica_standings":       JOLPICA_ENABLED,
    "jolpica_results":         JOLPICA_ENABLED,
    "jolpica_schedule":        JOLPICA_ENABLED,
    "apisports_fallback":      APISPORTS_ENABLED,
    "auto_update_after_race":  True,    # Auto-refresh data 2 hours after race end
    "cache_api_responses":     CACHE_ENABLED,
}

DATA_SOURCE_PRIORITY = ["openf1", "jolpica", "local"]


# ── Driver ID Mapping ─────────────────────────────────────────────────────────
# Maps our internal driver IDs to external API identifiers

# OpenF1 uses driver numbers (e.g., 1 = Verstappen, 44 = Hamilton)
DRIVER_ID_TO_OPENF1_NUMBER: Dict[str, int] = {
    "verstappen": 1,
    "perez": 11,
    "hamilton": 44,
    "leclerc": 16,
    "sainz": 55,
    "norris": 4,
    "piastri": 81,
    "alonso": 14,
    "stroll": 18,
    "russell": 63,
    "antonelli": 15,
    "gasly": 10,
    "ocon": 31,
    "tsunoda": 22,       # If applicable
    "lawson": 3,
    "hadjar": 6,
    "lindblad": 41,
    "hulkenberg": 27,
    "bortoleto": 5,
    "albon": 23,
    "bearman": 87,
    "colapinto": 43,
    "bottas": 77,
}

# Jolpica uses Ergast-style driver codes (lowercase)
DRIVER_ID_TO_JOLPICA: Dict[str, str] = {
    "verstappen": "max_verstappen",
    "perez": "perez",
    "hamilton": "hamilton",
    "leclerc": "leclerc",
    "sainz": "sainz",
    "norris": "norris",
    "piastri": "piastri",
    "alonso": "alonso",
    "stroll": "stroll",
    "russell": "russell",
    "antonelli": "antonelli",
    "gasly": "gasly",
    "ocon": "ocon",
    "lawson": "lawson",
    "hadjar": "hadjar",
    "lindblad": "lindblad",
    "hulkenberg": "hulkenberg",
    "bortoleto": "bortoleto",
    "albon": "albon",
    "bearman": "bearman",
    "colapinto": "colapinto",
    "bottas": "bottas",
}

# Maps our team IDs to Jolpica constructor IDs
TEAM_ID_TO_JOLPICA: Dict[str, str] = {
    "mercedes":     "mercedes",
    "ferrari":      "ferrari",
    "red_bull":     "red_bull",
    "mclaren":      "mclaren",
    "williams":     "williams",
    "alpine":       "alpine",
    "haas":         "haas",
    "aston_martin": "aston_martin",
    "audi":         "audi",
    "rb":           "rb",
    "cadillac":     "cadillac",
}


# ── Validation ────────────────────────────────────────────────────────────────

def validate_api_settings() -> Dict[str, Any]:
    """Validate API settings and return status report."""
    issues = []

    if not OPENF1_ENABLED and not JOLPICA_ENABLED:
        issues.append("Both OpenF1 and Jolpica are disabled — no live data sources available")

    if APISPORTS_ENABLED and not APISPORTS_API_KEY:
        issues.append("API-Sports enabled but no API key set in APISPORTS_F1_API_KEY env var")

    # Check cache directory
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        issues.append(f"Cannot create cache directory {CACHE_DIR}: {e}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "openf1_enabled": OPENF1_ENABLED,
        "jolpica_enabled": JOLPICA_ENABLED,
        "apisports_enabled": APISPORTS_ENABLED,
        "cache_dir": str(CACHE_DIR),
    }


def get_api_status() -> Dict[str, Any]:
    """Return a summary of all API source statuses."""
    return {
        "openf1": {
            "enabled": OPENF1_ENABLED,
            "base_url": OPENF1_BASE_URL,
            "rate_limit": f"{OPENF1_RATE_LIMIT_RPS} req/s, {OPENF1_RATE_LIMIT_RPM} req/min",
            "auth": "None (free, no key)",
        },
        "jolpica": {
            "enabled": JOLPICA_ENABLED,
            "base_url": JOLPICA_BASE_URL,
            "rate_limit": f"{JOLPICA_RATE_LIMIT_RPS} req/s, {JOLPICA_RATE_LIMIT_RPM} req/min",
            "auth": "None (free, no key)",
        },
        "apisports": {
            "enabled": APISPORTS_ENABLED,
            "base_url": APISPORTS_BASE_URL,
            "rate_limit": f"{APISPORTS_RATE_LIMIT_RPD} req/day",
            "auth": "API key required",
            "key_set": bool(APISPORTS_API_KEY),
        },
        "cache": {
            "enabled": CACHE_ENABLED,
            "directory": str(CACHE_DIR),
            "ttl_live": f"{CACHE_TTL_SECONDS}s",
            "ttl_standings": f"{CACHE_TTL_STANDINGS_SECONDS}s",
            "ttl_schedule": f"{CACHE_TTL_SCHEDULE_SECONDS}s",
            "ttl_historical": f"{CACHE_TTL_HISTORICAL_SECONDS}s",
        },
    }


# ── EXPORT ────────────────────────────────────────────────────────────────────

__all__ = [
    # OpenF1
    "OPENF1_BASE_URL", "OPENF1_RATE_LIMIT_RPS", "OPENF1_RATE_LIMIT_RPM",
    "OPENF1_TIMEOUT", "OPENF1_ENABLED", "OPENF1_ENDPOINTS",
    # Jolpica
    "JOLPICA_BASE_URL", "JOLPICA_RATE_LIMIT_RPS", "JOLPICA_RATE_LIMIT_RPM",
    "JOLPICA_TIMEOUT", "JOLPICA_ENABLED", "JOLPICA_ENDPOINTS",
    # API-Sports
    "APISPORTS_BASE_URL", "APISPORTS_API_KEY", "APISPORTS_RATE_LIMIT_RPD",
    "APISPORTS_TIMEOUT", "APISPORTS_ENABLED",
    # Cache
    "CACHE_DIR", "CACHE_ENABLED",
    "CACHE_TTL_SECONDS", "CACHE_TTL_LIVE_TIMING_SECONDS", "CACHE_TTL_LIVE_WEATHER_SECONDS",
    "CACHE_TTL_SESSION_RESULTS_SECONDS", "CACHE_TTL_STANDINGS_SECONDS",
    "CACHE_TTL_SCHEDULE_SECONDS", "CACHE_TTL_HISTORICAL_SECONDS",
    "DATA_SOURCE_PRIORITY",
    # Feature flags
    "FEATURE_FLAGS",
    # ID mappings
    "DRIVER_ID_TO_OPENF1_NUMBER", "DRIVER_ID_TO_JOLPICA", "TEAM_ID_TO_JOLPICA",
    # Validation
    "validate_api_settings", "get_api_status",
]
