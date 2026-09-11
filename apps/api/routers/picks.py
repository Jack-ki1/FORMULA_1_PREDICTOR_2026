"""
Fantasy league router — this is the feature described in PLAN.md §7:
`UserPick` and `LeaderboardEntry` already existed in the schema before
this migration but nothing ever read or wrote them. This wires them up.

Scoring happens in apps/ingest/evaluate_accuracy.py after each race, not
here — this router is just submit-a-pick / read-my-picks / read-the-
leaderboard.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from data.calendar_2026 import get_race_by_id
from config.team_driver_lineup_2026 import get_driver_by_code
from database.db import get_db
from database.models import User, UserPick, LeaderboardEntry
from routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_SESSIONS = {"qualifying", "race", "sprint"}
VALID_TARGETS = {"winner", "podium", "pole", "fastest_lap"}


class PickRequest(BaseModel):
    race_id: str
    session: str
    target: str
    driver_id: str


class PickResponse(BaseModel):
    id: int
    race_id: str
    session: str
    target: str
    driver_id: str
    status: str
    points: int


class LeaderboardRow(BaseModel):
    rank: int
    display_name: str
    avatar_url: str | None
    total_score: int
    picks_made: int
    picks_resolved: int


@router.post("/picks", response_model=PickResponse)
def submit_pick(
    body: PickRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    race = get_race_by_id(body.race_id)
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    if race.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Picks are closed — this race has already happened")
    if body.session not in VALID_SESSIONS:
        raise HTTPException(status_code=400, detail=f"session must be one of {sorted(VALID_SESSIONS)}")
    if body.target not in VALID_TARGETS:
        raise HTTPException(status_code=400, detail=f"target must be one of {sorted(VALID_TARGETS)}")
    if not get_driver_by_code(body.driver_id.upper()):
        raise HTTPException(status_code=400, detail="Unknown driver code")

    driver_id = body.driver_id.upper()
    existing = (
        db.query(UserPick)
        .filter(
            UserPick.user_id == current_user.id,
            UserPick.race_id == body.race_id,
            UserPick.session == body.session,
            UserPick.target == body.target,
        )
        .first()
    )
    if existing:
        existing.driver_id = driver_id
        pick = existing
    else:
        pick = UserPick(
            user_id=current_user.id,
            race_id=body.race_id,
            session=body.session,
            target=body.target,
            driver_id=driver_id,
        )
        db.add(pick)
        entry = db.query(LeaderboardEntry).filter(LeaderboardEntry.user_id == current_user.id).first()
        if entry:
            entry.picks_made = (entry.picks_made or 0) + 1

    db.commit()
    db.refresh(pick)
    return PickResponse(
        id=pick.id, race_id=pick.race_id, session=pick.session, target=pick.target,
        driver_id=pick.driver_id, status=pick.status, points=pick.points,
    )


@router.get("/picks", response_model=list[PickResponse])
def my_picks(
    race_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(UserPick).filter(UserPick.user_id == current_user.id)
    if race_id:
        query = query.filter(UserPick.race_id == race_id)
    rows = query.order_by(desc(UserPick.made_at)).all()
    return [
        PickResponse(
            id=r.id, race_id=r.race_id, session=r.session, target=r.target,
            driver_id=r.driver_id, status=r.status, points=r.points,
        )
        for r in rows
    ]


@router.get("/leaderboard", response_model=list[LeaderboardRow])
def leaderboard(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(LeaderboardEntry)
        .join(User, User.id == LeaderboardEntry.user_id)
        .order_by(desc(LeaderboardEntry.total_score))
        .limit(min(limit, 200))
        .all()
    )
    return [
        LeaderboardRow(
            rank=i + 1,
            display_name=row.user.display_name,
            avatar_url=row.user.avatar_url,
            total_score=row.total_score,
            picks_made=row.picks_made,
            picks_resolved=row.picks_resolved,
        )
        for i, row in enumerate(rows)
    ]
