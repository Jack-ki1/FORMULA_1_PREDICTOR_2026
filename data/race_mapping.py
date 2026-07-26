"""
Race Name Mapping — Single Source of Truth.

Maps display names (e.g., "Australian Grand Prix") to circuit IDs (e.g., "australia").
Used by dashboard API endpoints and frontend race selectors.

Usage:
    from data.race_mapping import RACE_NAME_MAPPING, get_circuit_id
    
    circuit_id = get_circuit_id("Australian Grand Prix")  # Returns "australia"
"""

from typing import Optional

# Canonical mapping from display names to circuit IDs
RACE_NAME_MAPPING = {
    "Australian Grand Prix": "australia",
    "Chinese Grand Prix": "china",
    "Japanese Grand Prix": "japan",
    "Bahrain Grand Prix": "bahrain",
    "Saudi Arabian Grand Prix": "saudi_arabia",
    "Miami Grand Prix": "miami",
    "Monaco Grand Prix": "monaco",
    "Spanish Grand Prix": "spain",
    "Canadian Grand Prix": "canada",
    "Austrian Grand Prix": "austria",
    "British Grand Prix": "britain",
    "Belgian Grand Prix": "belgium",
    "Hungarian Grand Prix": "hungary",
    "Dutch Grand Prix": "netherlands",
    "Italian Grand Prix": "italy",           # Italian GP is at Monza
    "Madrid Grand Prix": "madrid",
    "Azerbaijan Grand Prix": "azerbaijan",
    "Singapore Grand Prix": "singapore",
    "United States Grand Prix": "usa",
    "Mexico City Grand Prix": "mexico",
    "São Paulo Grand Prix": "brazil",
    "Las Vegas Grand Prix": "las_vegas",
    "Qatar Grand Prix": "qatar",
    "Abu Dhabi Grand Prix": "uae",
}


def get_circuit_id(race_name: str) -> str:
    """
    Get circuit ID from race display name.
    
    Args:
        race_name: Display name like "Australian Grand Prix"
    
    Returns:
        Circuit ID like "australia", or None if not found
    """
    return RACE_NAME_MAPPING.get(race_name)


def get_all_race_names() -> list:
    """Get sorted list of all race display names."""
    return sorted(RACE_NAME_MAPPING.keys())


def get_all_circuit_ids() -> list:
    """Get list of all unique circuit IDs."""
    return list(set(RACE_NAME_MAPPING.values()))


# Reverse mapping from circuit ID back to display name (e.g. "australia" -> "Australian
# Grand Prix"). Built once at import time; safe because RACE_NAME_MAPPING above is 1:1
# (each circuit ID appears under exactly one display name).
CIRCUIT_ID_TO_RACE_NAME = {v: k for k, v in RACE_NAME_MAPPING.items()}


def get_race_name(circuit_id: str) -> Optional[str]:
    """
    Get the display race name for a circuit ID (inverse of get_circuit_id).

    Args:
        circuit_id: Circuit ID like "australia"

    Returns:
        Display name like "Australian Grand Prix", or None if not found
    """
    return CIRCUIT_ID_TO_RACE_NAME.get(circuit_id)
