"""
2026 F1 World Championship — Full Calendar.

Status values: "completed" | "upcoming" | "tbc"

FastF1 Integration: This calendar can now sync with FastF1's official schedule
to automatically update race statuses and ensure accuracy.
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Try to import FastF1
try:
    import fastf1
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    logger.warning("FastF1 not available. Calendar sync will be disabled.")


CALENDAR_2026: list = [
    {"round": 1,  "circuit": "australia",   "name": "Australian Grand Prix",      "date": "2026-03-08", "sprint": False, "status": "completed"},
    {"round": 2,  "circuit": "china",        "name": "Chinese Grand Prix",         "date": "2026-03-15", "sprint": True,  "status": "completed"},
    {"round": 3,  "circuit": "japan",        "name": "Japanese Grand Prix",        "date": "2026-04-06", "sprint": False, "status": "completed"},
    {"round": 4,  "circuit": "bahrain",      "name": "Bahrain Grand Prix",         "date": "2026-04-12", "sprint": False, "status": "completed"},
    {"round": 5,  "circuit": "miami",        "name": "Miami Grand Prix",           "date": "2026-05-03", "sprint": True,  "status": "completed"},
    {"round": 6,  "circuit": "canada",       "name": "Canadian Grand Prix",        "date": "2026-05-24", "sprint": True, "status": "completed"},  # Updated to reflect actual date and sprint status
    {"round": 7,  "circuit": "monaco",       "name": "Monaco Grand Prix",          "date": "2026-06-07", "sprint": False, "status": "upcoming"},
    {"round": 8,  "circuit": "spain",        "name": "Spanish Grand Prix (Barcelona)", "date": "2026-06-14", "sprint": False, "status": "upcoming"},
    {"round": 9,  "circuit": "austria",      "name": "Austrian Grand Prix",        "date": "2026-06-28", "sprint": True,  "status": "upcoming"},
    {"round": 10, "circuit": "britain",      "name": "British Grand Prix",         "date": "2026-07-05", "sprint": True,  "status": "upcoming"},
    {"round": 11, "circuit": "hungary",      "name": "Hungarian Grand Prix",       "date": "2026-07-19", "sprint": False, "status": "upcoming"},
    {"round": 12, "circuit": "belgium",      "name": "Belgian Grand Prix",         "date": "2026-07-26", "sprint": False, "status": "upcoming"},
    {"round": 13, "circuit": "netherlands",  "name": "Dutch Grand Prix",           "date": "2026-08-30", "sprint": True,  "status": "upcoming"},
    {"round": 14, "circuit": "italy",        "name": "Italian Grand Prix",         "date": "2026-09-06", "sprint": False, "status": "upcoming"},
    {"round": 15, "circuit": "madrid",       "name": "Spanish Grand Prix (Madrid)", "date": "2026-09-13", "sprint": False, "status": "upcoming"},
    {"round": 16, "circuit": "azerbaijan",   "name": "Azerbaijan Grand Prix",      "date": "2026-09-20", "sprint": False, "status": "upcoming"},
    {"round": 17, "circuit": "singapore",    "name": "Singapore Grand Prix",       "date": "2026-10-04", "sprint": True,  "status": "upcoming"},
    {"round": 18, "circuit": "usa",          "name": "United States Grand Prix",   "date": "2026-10-18", "sprint": False, "status": "upcoming"},
    {"round": 19, "circuit": "mexico",       "name": "Mexico City Grand Prix",     "date": "2026-10-25", "sprint": False, "status": "upcoming"},
    {"round": 20, "circuit": "brazil",       "name": "São Paulo Grand Prix",       "date": "2026-11-08", "sprint": True,  "status": "upcoming"},
    {"round": 21, "circuit": "las_vegas",    "name": "Las Vegas Grand Prix",       "date": "2026-11-21", "sprint": False, "status": "upcoming"},
    {"round": 22, "circuit": "qatar",        "name": "Qatar Grand Prix",           "date": "2026-11-29", "sprint": True,  "status": "upcoming"},
    {"round": 23, "circuit": "uae",          "name": "Abu Dhabi Grand Prix",       "date": "2026-12-06", "sprint": False, "status": "upcoming"},
]

# ── FastF1 Sync Functions ─────────────────────────────────────────────────

def sync_calendar_from_fastf1(season: int = 2026) -> Dict[str, Any]:
    """
    Update calendar status from FastF1's official schedule.
    
    This function:
    1. Fetches the official F1 schedule from FastF1
    2. Compares with local calendar
    3. Updates race statuses (completed/upcoming)
    4. Adds any missing races
    
    Args:
        season: Year to sync (default: 2026)
    
    Returns:
        Dictionary with sync results:
        - synced: Number of races updated
        - added: Number of new races added
        - errors: List of any errors encountered
    """
    if not FASTF1_AVAILABLE:
        logger.warning("FastF1 not available. Cannot sync calendar.")
        return {"synced": 0, "added": 0, "errors": ["FastF1 not installed"]}
    
    try:
        # Fetch official schedule from FastF1
        schedule = fastf1.get_event_schedule(season)
        
        synced = 0
        added = 0
        errors = []
        
        today = datetime.now().date()
        
        for idx, event in schedule.iterrows():
            # Skip non-race events if necessary, though usually EventName handles GP names
            # Pre-Season Test is usually RoundNumber 0 or similar, but checking name is safer
            if 'Test' in event['EventName']:
                continue
            
            round_num = int(event['RoundNumber'])
            event_name = event['EventName']
            event_date = event['EventDate']
            
            # Ensure event_date is a date object
            if hasattr(event_date, 'date'):
                race_date = event_date.date()
            elif isinstance(event_date, str):
                race_date = datetime.strptime(event_date, '%Y-%m-%d').date()
            else:
                race_date = event_date

            # Find matching race in local calendar
            local_race = next((r for r in CALENDAR_2026 if r['round'] == round_num), None)
            
            if local_race:
                # Update existing race status based on date
                old_status = local_race['status']
                # Determine new status: if race date is in the past, it's completed (unless it was TBC and we want to keep TBC logic, but simple completed/upcoming is requested)
                # Note: In F1 context, "completed" usually means the race weekend is over.
                new_status = "completed" if race_date < today else "upcoming"
                
                # Only update if status actually changes to avoid unnecessary dirtying
                if old_status != new_status:
                    local_race['status'] = new_status
                    synced += 1
                    logger.info(f"Updated {event_name} (Round {round_num}): {old_status} → {new_status}")
            else:
                # Add new race to calendar if not present
                # Generate a simple circuit key
                circuit_key = event_name.lower().replace(' ', '_').replace('_grand_prix', '').replace('_gp', '')
                
                new_race = {
                    "round": round_num,
                    "circuit": circuit_key,
                    "name": event_name,
                    "date": str(event_date),
                    "sprint": False,  # FastF1 schedule doesn't explicitly flag sprints easily without deeper inspection
                    "status": "completed" if race_date < today else "upcoming"
                }
                CALENDAR_2026.append(new_race)
                added += 1
                logger.info(f"Added new race: {event_name}")
        
        # Sort calendar by round number
        CALENDAR_2026.sort(key=lambda x: x['round'])
        
        result = {
            "synced": synced,
            "added": added,
            "errors": errors,
            "total_races": len(CALENDAR_2026)
        }
        
        logger.info(f"Calendar sync completed: {synced} updated, {added} added")
        return result
        
    except Exception as e:
        error_msg = f"Calendar sync failed: {e}"
        logger.error(error_msg)
        return {"synced": 0, "added": 0, "errors": [error_msg]}


def get_fastf1_session(round_or_name: Any, session_type: str = 'R'):
    """
    Helper function to get FastF1 session using calendar data.
    
    Args:
        round_or_name: Round number (int) or circuit ID (str)
        session_type: Session type ('P1', 'P2', 'P3', 'Q', 'S', 'R')
    
    Returns:
        FastF1 session object
    """
    if not FASTF1_AVAILABLE:
        raise ImportError("FastF1 not installed. Install with: pip install fastf1")
    
    # Find race in calendar
    race = None
    if isinstance(round_or_name, int):
        race = get_race_by_round(round_or_name)
    else:
        # Assume it's a circuit key or name
        race = next((r for r in CALENDAR_2026 if r['circuit'] == round_or_name or r['name'] == round_or_name), None)
    
    if race is None:
        raise ValueError(f"Race not found in local calendar: {round_or_name}")
    
    # Get session from FastF1
    # fastf1.get_session expects year, identifier (name or round), session
    try:
        session = fastf1.get_session(2026, race['name'], session_type)
        session.load()
        return session
    except Exception as e:
        logger.error(f"Failed to load session for {race['name']} {session_type}: {e}")
        raise


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


def get_sprint_weekends() -> list:
    """Return all sprint format rounds."""
    return [r for r in CALENDAR_2026 if r["sprint"]]


def get_completed_races() -> list:
    return [r for r in CALENDAR_2026 if r["status"] == "completed"]