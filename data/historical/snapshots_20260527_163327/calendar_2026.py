"""
2026 F1 World Championship — Full Calendar.

Status values: "completed" | "upcoming" | "tbc"
"""

CALENDAR_2026: list = [
    {"round": 1,  "circuit": "australia",   "name": "Australian Grand Prix",      "date": "2026-03-08", "sprint": False, "status": "completed"},
    {"round": 2,  "circuit": "china",        "name": "Chinese Grand Prix",         "date": "2026-03-15", "sprint": True,  "status": "completed"},
    {"round": 3,  "circuit": "japan",        "name": "Japanese Grand Prix",        "date": "2026-04-06", "sprint": False, "status": "completed"},
    {"round": 4,  "circuit": "bahrain",      "name": "Bahrain Grand Prix",         "date": "2026-04-12", "sprint": False, "status": "completed"},
    {"round": 5,  "circuit": "saudi_arabia", "name": "Saudi Arabian Grand Prix",   "date": "2026-04-26", "sprint": True,  "status": "completed"},
    {"round": 6,  "circuit": "miami",        "name": "Miami Grand Prix",           "date": "2026-05-03", "sprint": True,  "status": "completed"},
    {"round": 7,  "circuit": "canada",       "name": "Canadian Grand Prix",        "date": "2026-05-17", "sprint": True,  "status": "upcoming"},
    {"round": 8,  "circuit": "monaco",       "name": "Monaco Grand Prix",          "date": "2026-06-07", "sprint": False, "status": "upcoming"},
    {"round": 9,  "circuit": "spain",        "name": "Spanish Grand Prix (Barcelona)", "date": "2026-06-14", "sprint": False, "status": "upcoming"},
    {"round": 10, "circuit": "austria",      "name": "Austrian Grand Prix",        "date": "2026-06-28", "sprint": True,  "status": "upcoming"},
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
    {"round": 21, "circuit": "brazil",       "name": "São Paulo Grand Prix",       "date": "2026-11-08", "sprint": True,  "status": "upcoming"},
    {"round": 22, "circuit": "las_vegas",    "name": "Las Vegas Grand Prix",       "date": "2026-11-21", "sprint": False, "status": "upcoming"},
    {"round": 23, "circuit": "qatar",        "name": "Qatar Grand Prix",           "date": "2026-11-29", "sprint": True,  "status": "upcoming"},
    {"round": 24, "circuit": "uae",          "name": "Abu Dhabi Grand Prix",       "date": "2026-12-06", "sprint": False, "status": "upcoming"},
]

def get_upcoming_races() -> list:
    """Return all races not yet completed."""
    return [r for r in CALENDAR_2026 if r["status"] == "upcoming"]


def get_next_race() -> dict | None:
    """Return the next upcoming race."""
    upcoming = get_upcoming_races()
    return upcoming[0] if upcoming else None


def get_race_by_round(round_number: int) -> dict | None:
    """Return a specific round."""
    return next((r for r in CALENDAR_2026 if r["round"] == round_number), None)


def get_sprint_weekends() -> list:
    """Return all sprint format rounds."""
    return [r for r in CALENDAR_2026 if r["sprint"]]


def get_completed_races() -> list:
    return [r for r in CALENDAR_2026 if r["status"] == "completed"]
