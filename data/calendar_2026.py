"""
2026 F1 World Championship — Full Calendar.

Status values: "completed" | "upcoming" | "tbc"
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


CALENDAR_2026: list = [
    {"round": 1,  "circuit": "australia",   "name": "Australian Grand Prix",      "date": "2026-03-08", "sprint": False, "status": "completed"},
    {"round": 2,  "circuit": "china",        "name": "Chinese Grand Prix",         "date": "2026-03-15", "sprint": True,  "status": "completed"},
    {"round": 3,  "circuit": "japan",        "name": "Japanese Grand Prix",        "date": "2026-04-06", "sprint": False, "status": "completed"},
    {"round": 4,  "circuit": "bahrain",      "name": "Bahrain Grand Prix",         "date": "2026-04-12", "sprint": False, "status": "completed"},
    # FIX: Saudi Arabian GP was missing entirely, which shifted every round number
    # below by one relative to circuit_data.py's round_2026 (the field actually used
    # to query Jolpica for results) — restored using circuit_data.py as source of truth.
    {"round": 5,  "circuit": "saudi_arabia", "name": "Saudi Arabian Grand Prix",   "date": "2026-04-26", "sprint": False, "status": "completed"},
    {"round": 6,  "circuit": "miami",        "name": "Miami Grand Prix",           "date": "2026-05-03", "sprint": True,  "status": "completed"},
    {"round": 7,  "circuit": "canada",       "name": "Canadian Grand Prix",        "date": "2026-05-24", "sprint": True, "status": "completed"},  # Updated to reflect actual date and sprint status
    {"round": 8,  "circuit": "monaco",       "name": "Monaco Grand Prix",          "date": "2026-06-07", "sprint": False, "status": "upcoming"},
    {"round": 9,  "circuit": "spain",        "name": "Spanish Grand Prix (Barcelona)", "date": "2026-06-14", "sprint": False, "status": "upcoming"},
    # FIX: Austria is not part of the official 2026 F1 Sprint calendar (only China,
    # Miami, Canada, Great Britain, Netherlands, and Singapore host sprints in 2026).
    {"round": 10, "circuit": "austria",      "name": "Austrian Grand Prix",        "date": "2026-06-28", "sprint": False,  "status": "upcoming"},
    {"round": 11, "circuit": "britain",      "name": "British Grand Prix",         "date": "2026-07-05", "sprint": True,  "status": "upcoming"},
    {"round": 12, "circuit": "hungary",      "name": "Hungarian Grand Prix",       "date": "2026-07-19", "sprint": False, "status": "upcoming"},
    {"round": 13, "circuit": "belgium",      "name": "Belgian Grand Prix",         "date": "2026-07-26", "sprint": False, "status": "upcoming"},
    {"round": 14, "circuit": "netherlands",  "name": "Dutch Grand Prix",           "date": "2026-08-30", "sprint": True,  "status": "upcoming"},
    {"round": 15, "circuit": "italy",        "name": "Italian Grand Prix",         "date": "2026-09-06", "sprint": False, "status": "upcoming"},
    {"round": 16, "circuit": "madrid",       "name": "Spanish Grand Prix (Madrid)", "date": "2026-09-13", "sprint": False, "status": "upcoming"},
    {"round": 17, "circuit": "azerbaijan",   "name": "Azerbaijan Grand Prix",      "date": "2026-09-20", "sprint": False, "status": "upcoming"},
    {"round": 18, "circuit": "singapore",    "name": "Singapore Grand Prix",       "date": "2026-10-04", "sprint": True,  "status": "upcoming"},
    {"round": 19, "circuit": "usa",          "name": "United States Grand Prix",   "date": "2026-10-18", "sprint": False, "status": "upcoming"},
    {"round": 20, "circuit": "mexico",       "name": "Mexico City Grand Prix",     "date": "2026-10-25", "sprint": False, "status": "upcoming"},
    # FIX: Brazil/São Paulo and Qatar are not part of the official 2026 F1 Sprint calendar.
    {"round": 21, "circuit": "brazil",       "name": "São Paulo Grand Prix",       "date": "2026-11-08", "sprint": False,  "status": "upcoming"},
    {"round": 22, "circuit": "las_vegas",    "name": "Las Vegas Grand Prix",       "date": "2026-11-21", "sprint": False, "status": "upcoming"},
    {"round": 23, "circuit": "qatar",        "name": "Qatar Grand Prix",           "date": "2026-11-29", "sprint": False,  "status": "upcoming"},
    {"round": 24, "circuit": "uae",          "name": "Abu Dhabi Grand Prix",       "date": "2026-12-06", "sprint": False, "status": "upcoming"},
]




# ── Calendar Query Functions ────────────────────────────────────────────────────

def get_upcoming_races() -> list:
    """Return all races not yet completed."""
    return [r for r in CALENDAR_2026 if r["status"] == "upcoming"]


def get_next_race() -> Optional[dict]:
    """Return the next upcoming race."""
    upcoming = get_upcoming_races()
    return upcoming[0] if upcoming else None


def get_race_by_round(round_number: int) -> Optional[dict]:
    """Return a specific round."""
    return next((r for r in CALENDAR_2026 if r["round"] == round_number), None)


def get_race_by_circuit(circuit_id: str) -> Optional[dict]:
    """Return the local race dictionary for a given circuit ID."""
    return next(
        (r for r in CALENDAR_2026 if r["circuit"] == circuit_id or r["name"].lower().replace(' ', '_') == circuit_id),
        None,
    )


def get_sprint_weekends() -> list:
    """Return all sprint format rounds."""
    return [r for r in CALENDAR_2026 if r["sprint"]]


def get_completed_races() -> list:
    return [r for r in CALENDAR_2026 if r["status"] == "completed"]


# ── Jolpica Calendar Sync ──────────────────────────────────────────────────────

def sync_calendar_from_jolpica() -> Dict[str, Any]:
    """
    Sync calendar status from Jolpica-F1 API schedule.
    
    Fetches the current season schedule from Jolpica and updates
    CALENDAR_2026 race statuses based on actual race dates.
    
    This is more reliable than FastF1 for schedule sync because:
    - It doesn't require loading session data
    - It's faster (single API call)
    - It works even when FastF1 data isn't available yet
    
    Returns:
        Dict with sync results: updated, added, errors
    """
    global CALENDAR_2026
    
    try:
        from data.jolpica_client import get_jolpica_client
        client = get_jolpica_client()
        
        schedule = client.get_current_schedule()
        if not schedule:
            return {"updated": 0, "added": 0, "errors": ["No schedule data from Jolpica"]}
        
        today = datetime.now().date()
        updated = 0
        added = 0
        errors = []
        
        # Update existing calendar entries
        for jolpica_race in schedule:
            round_num = jolpica_race["round"]
            
            # Find matching entry in our calendar
            local_race = next((r for r in CALENDAR_2026 if r["round"] == round_num), None)
            
            if local_race:
                # Update status based on date
                try:
                    race_date = datetime.strptime(jolpica_race["date"], "%Y-%m-%d").date()
                    new_status = "completed" if race_date <= today else "upcoming"
                    
                    if local_race["status"] != new_status:
                        local_race["status"] = new_status
                        updated += 1
                        logger.info(f"Calendar updated: Round {round_num} {local_race['name']} → {new_status}")
                except (ValueError, KeyError) as e:
                    errors.append(f"Round {round_num}: {e}")
            else:
                # Add missing race
                try:
                    race_date = datetime.strptime(jolpica_race["date"], "%Y-%m-%d").date()
                    status = "completed" if race_date <= today else "upcoming"
                    
                    new_race = {
                        "round": round_num,
                        "circuit": jolpica_race.get("circuit_id", f"round_{round_num}"),
                        "name": jolpica_race["race_name"],
                        "date": jolpica_race["date"],
                        "sprint": False,  # Jolpica doesn't provide sprint info
                        "status": status,
                    }
                    CALENDAR_2026.append(new_race)
                    added += 1
                    logger.info(f"Calendar added: Round {round_num} {jolpica_race['race_name']}")
                except Exception as e:
                    errors.append(f"Round {round_num}: {e}")
        
        # Sort calendar by round number
        CALENDAR_2026.sort(key=lambda r: r["round"])
        
        result = {
            "updated": updated,
            "added": added,
            "errors": errors,
            "source": "jolpica",
            "total_races": len(CALENDAR_2026),
        }
        
        logger.info(f"Calendar synced from Jolpica: {updated} updated, {added} added")
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync calendar from Jolpica: {e}")
        return {"updated": 0, "added": 0, "errors": [str(e)], "source": "error"}


def get_next_race_from_api() -> Optional[Dict[str, Any]]:
    """
    Get the next upcoming race from Jolpica API.
    
    More reliable than get_next_race() because it uses live schedule data.
    
    Returns:
        Dict with next race info, or None if no upcoming races
    """
    try:
        from data.jolpica_client import get_jolpica_client
        client = get_jolpica_client()
        
        schedule = client.get_current_schedule()
        if not schedule:
            return None
        
        today = datetime.now().date()
        
        for race in schedule:
            try:
                race_date = datetime.strptime(race["date"], "%Y-%m-%d").date()
                if race_date > today:
                    return {
                        "round": race["round"],
                        "name": race["race_name"],
                        "circuit": race.get("circuit_id", ""),
                        "date": race["date"],
                        "time": race.get("time", ""),
                        "source": "jolpica",
                    }
            except (ValueError, KeyError):
                continue
        
        return None
        
    except Exception as e:
        logger.debug(f"Failed to get next race from API: {e}")
        # Fallback to local data
        return get_next_race()
