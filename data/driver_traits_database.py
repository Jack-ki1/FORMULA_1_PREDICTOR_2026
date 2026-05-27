"""
Driver Traits Database — Historical performance and circuit affinity data.

Provides access to driver-specific historical data including:
  - Circuit affinity scores
  - Historical finish positions at specific tracks
  - Wins, podiums, poles at each circuit
  - Confidence ratings based on sample size
"""

from typing import Optional, Dict, Any


# Placeholder database - can be populated with real historical data later
DRIVER_TRAITS_DB: Dict[str, Dict[str, Dict[str, Any]]] = {
    # Example structure (currently empty):
    # "hamilton": {
    #     "circuit_affinity": {
    #         "canada": {
    #             "avg_finish": 2.5,
    #             "wins": 7,
    #             "podiums": 12,
    #             "poles": 6,
    #             "confidence_rating": 0.95,
    #             "races_completed": 15,
    #         }
    #     }
    # }
}


def get_driver_trait(
    driver_id: str,
    trait_type: str,
    circuit_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve driver trait data from the database.
    
    Args:
        driver_id: Driver identifier (e.g., 'hamilton', 'verstappen')
        trait_type: Type of trait to retrieve (e.g., 'circuit_affinity')
        circuit_id: Optional circuit identifier for circuit-specific traits
    
    Returns:
        Dictionary containing trait data, or None if not found
    """
    if driver_id not in DRIVER_TRAITS_DB:
        return None
    
    driver_data = DRIVER_TRAITS_DB[driver_id]
    
    if trait_type not in driver_data:
        return None
    
    trait_data = driver_data[trait_type]
    
    # If circuit_id is provided and trait is circuit-specific
    if circuit_id and isinstance(trait_data, dict):
        return trait_data.get(circuit_id)
    
    # Otherwise return the entire trait dataset
    return trait_data if isinstance(trait_data, dict) else None


def add_driver_circuit_data(
    driver_id: str,
    circuit_id: str,
    avg_finish: Optional[float] = None,
    wins: int = 0,
    podiums: int = 0,
    poles: int = 0,
    races_completed: int = 0,
) -> None:
    """
    Add or update circuit-specific data for a driver.
    
    Args:
        driver_id: Driver identifier
        circuit_id: Circuit identifier
        avg_finish: Average finishing position
        wins: Number of wins at this circuit
        podiums: Number of podiums at this circuit
        poles: Number of pole positions at this circuit
        races_completed: Total races completed at this circuit
    """
    if driver_id not in DRIVER_TRAITS_DB:
        DRIVER_TRAITS_DB[driver_id] = {"circuit_affinity": {}}
    
    if "circuit_affinity" not in DRIVER_TRAITS_DB[driver_id]:
        DRIVER_TRAITS_DB[driver_id]["circuit_affinity"] = {}
    
    confidence = min(1.0, races_completed / 10.0) if races_completed > 0 else None
    
    DRIVER_TRAITS_DB[driver_id]["circuit_affinity"][circuit_id] = {
        "avg_finish": avg_finish,
        "wins": wins,
        "podiums": podiums,
        "poles": poles,
        "confidence_rating": confidence,
        "races_completed": races_completed,
    }


# ── EXPORT ──────────────────────────────────────────────────────────────────────

__all__ = ["get_driver_trait", "add_driver_circuit_data", "DRIVER_TRAITS_DB"]
