"""
A lightweight "is the data fresh, how's the model doing" status endpoint.

This intentionally replaces the old Flask app's `monitoring/blueprint.py`
(a Prometheus `/metrics` endpoint that was never registered/reachable —
see AUDIT.md m-3) rather than porting it as-is: nothing in this stack
runs a Prometheus server to scrape it, so a real Prometheus exporter
would be 100% unused surface area. This gets most of the practical value
(a "synced N minutes ago" indicator + model accuracy the frontend can
show in a status strip) for a fraction of the moving parts. A real
Prometheus/Grafana setup is a reasonable thing to add later if this ever
needs to be operated by more than one person — noted in the README, not
built speculatively now.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import ModelRun
from models.prediction import SessionData

router = APIRouter()


@router.get("/status")
def status(db: Session = Depends(get_db)):
    latest_sync = db.query(func.max(SessionData.updated_at)).scalar()

    latest_runs_by_target = {}
    for target in ("winner", "podium", "points", "q3"):
        run = (
            db.query(ModelRun)
            .filter(ModelRun.target == target)
            .order_by(ModelRun.created_at.desc())
            .first()
        )
        if run:
            latest_runs_by_target[target] = {
                "accuracy": run.accuracy,
                "baseline": run.baseline,
                "model_version": run.model_version,
                "backtest_season": run.backtest_season,
                "evaluated_at": run.created_at.isoformat() if run.created_at else None,
            }

    now = datetime.now(timezone.utc)
    minutes_since_sync = None
    if latest_sync:
        sync_dt = latest_sync if latest_sync.tzinfo else latest_sync.replace(tzinfo=timezone.utc)
        minutes_since_sync = round((now - sync_dt).total_seconds() / 60, 1)

    return {
        "data_last_synced_at": latest_sync.isoformat() if latest_sync else None,
        "minutes_since_last_sync": minutes_since_sync,
        "model_runs": latest_runs_by_target,
        "checked_at": now.isoformat(),
    }
