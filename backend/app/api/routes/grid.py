from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/grid", tags=["grid"])

@router.get("/{race_id}")
async def get_grid(race_id: str, season: int = 2026):
    """
    Official grid from F1 — Jolpica qualifying, fallback to simulated.
    Used by manual grid editor as primary, manual as fallback.
    """
    try:
        from backend.app.data.calendar_2026 import get_race_by_id
        race = get_race_by_id(race_id)
        if not race:
            return JSONResponse({"error":{"code":"NOT_FOUND","message":"Unknown race"}}, status_code=404)
        round_no = race.get("round", 1)
        from backend.app.engine.grid_model import GridModel
        gm = GridModel()
        res = gm.get_grid_positions(season=season, round_number=round_no, use_real_qualifying=True)
        grid = res.get("grid", {})
        source = res.get("source","simulated")
        method = res.get("method","simulated_qualifying")
        # Normalize to sorted list
        items = sorted(grid.items(), key=lambda x: x[1]) if grid else []
        return {
            "race_id": race_id,
            "round": round_no,
            "season": season,
            "grid": grid,
            "ordered": [{"code": code, "position": pos} for code,pos in items],
            "source": source,
            "method": method,
            "provenance": f"{source} via {'Jolpica' if source=='live' else 'simulated Q1-Q3 (22→16→10)'}",
            "fallback_note": "Manual grid is fallback when official not yet available (2026 future races)"
        }
    except Exception as e:
        return JSONResponse({"error":{"code":"GRID_FAILED","message":str(e)}}, status_code=500)
