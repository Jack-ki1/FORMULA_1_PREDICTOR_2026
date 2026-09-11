"""Constructors router — ports dashboard/blueprints/constructors.py."""
from fastapi import APIRouter

from data.team_data import get_all_enhanced_teams, get_team_power_rankings

router = APIRouter()


@router.get("/teams")
def teams():
    return get_all_enhanced_teams()


@router.get("/power-rankings")
def power_rankings():
    return get_team_power_rankings()
