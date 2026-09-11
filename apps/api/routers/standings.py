"""Standings router — ports dashboard/blueprints/standings.py."""
import logging

from fastapi import APIRouter

from config.settings import settings
from data.season_2026 import get_driver_standings, get_constructor_standings
from data.jolpica_client import JolpicaClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/drivers")
def driver_standings():
    try:
        client = JolpicaClient()
        result = client.get_driver_standings(settings.SEASON_YEAR)
        if result.get("source") == "live":
            return result
    except Exception as e:
        logger.warning(f"Live driver standings fetch failed, using local data: {e}")

    return {"data": get_driver_standings(), "source": "local"}


@router.get("/constructors")
def constructor_standings():
    try:
        client = JolpicaClient()
        result = client.get_constructor_standings()
        if result.get("source") == "live":
            return result
    except Exception as e:
        logger.warning(f"Live constructor standings fetch failed, using local data: {e}")

    return {"data": get_constructor_standings(), "source": "local"}
