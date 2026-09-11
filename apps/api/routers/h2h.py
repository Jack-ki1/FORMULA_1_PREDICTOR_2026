"""H2H router — ports dashboard/blueprints/h2h.py (already fixed once
during the Flask-era audit; that fix carries forward unchanged)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.elo_calculator import elo_calculator
from config.team_driver_lineup_2026 import get_all_drivers, get_driver_by_code

router = APIRouter()


class CompareRequest(BaseModel):
    driver_a: str
    driver_b: str


@router.get("/drivers")
def list_drivers():
    return get_all_drivers()


@router.post("/compare")
def compare(body: CompareRequest):
    driver_a = body.driver_a.upper()
    driver_b = body.driver_b.upper()

    driver_a_info = get_driver_by_code(driver_a)
    driver_b_info = get_driver_by_code(driver_b)
    if not driver_a_info or not driver_b_info:
        raise HTTPException(status_code=404, detail="Unknown driver code")

    probability = elo_calculator.get_h2h_probability(driver_a, driver_b)
    return {
        "driver_a": driver_a_info,
        "driver_b": driver_b_info,
        "win_probability": probability,
        "reverse_probability": 1 - probability,
    }
