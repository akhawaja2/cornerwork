import os
from datetime import datetime, time, timedelta, timezone
from statistics import median

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.models import Athlete, Event, Flag, Gym, utcnow

router = APIRouter(prefix="/api/owner")
GYM_SHARE_USD = float(os.environ.get("GYM_SHARE_USD", "10"))  # $25 add-on: $10 coach, $5 Cornerwork, $10 gym (docs/08 §5)


@router.get("/summary")
def summary(session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Owner numbers. Every figure derives from the events table; athlete status is the only state read."""
    now = utcnow()
    week = now - timedelta(days=7)
    athletes = session.exec(select(Athlete).where(Athlete.gym_id == gym.id)).all()
    events = session.exec(select(Event).where(Event.gym_id == gym.id)).all()
    active = {a.id for a in athletes if a.status == "active"}
    logs = [e for e in events if e.type == "log_received"]
    replies = [e for e in events if e.type == "reply_sent"]
    secs = [e.meta["reply_seconds"] for e in replies if e.meta.get("reply_seconds") is not None]  # migrated replies have no time
    weekly_loggers = {e.athlete_id for e in logs if e.at >= week} & active
    last_activity = {}
    for e in events:
        if e.type in ("log_received", "check_in") and e.athlete_id:
            last_activity[e.athlete_id] = max(e.at, last_activity.get(e.athlete_id, e.at))
    asked = {f.athlete_id for f in session.exec(select(Flag).where(Flag.type == "drift", Flag.resolved_at == None)).all()}
    drift = []
    for a in athletes:
        if a.id not in active:
            continue
        last = last_activity.get(a.id) or datetime.combine(a.membership_start or a.created_at.date(), time(), tzinfo=timezone.utc)
        if (now - last).days >= 10:
            month = ((now.date() - a.membership_start).days // 30 + 1) if a.membership_start else None
            drift.append({"id": a.id, "name": a.name, "days_inactive": (now - last).days, "last_activity": last,
                          "month": month, "asked": a.id in asked})
    by_coach = {}
    for e in replies:
        if e.meta.get("reply_seconds") is not None:
            by_coach.setdefault(e.user_id, []).append(e.meta["reply_seconds"])
    return {
        "period_days": 7, "computed_from": "events",
        "roster": len(athletes), "coached": len(active),
        "revenue_estimate_usd": round(len(active) * GYM_SHARE_USD), "gym_share_usd": GYM_SHARE_USD,
        "opt_ins": len({e.athlete_id for e in events if e.type == "opt_in"}),
        "weekly_loggers": len(weekly_loggers),
        "weekly_logging_rate": round(len(weekly_loggers) / len(active) * 100, 1) if active else None,
        "total_logs": len(logs), "total_replies": len(replies), "unanswered_logs": max(0, len(logs) - len(replies)),
        "reply_rate": round(len(replies) / len(logs) * 100, 1) if logs else None,
        "median_reply_seconds": int(median(secs)) if secs else None,
        "replied_within_48h_rate": round(sum(s <= 172800 for s in secs) / len(logs) * 100, 1) if logs else None,
        "drift": drift,
        "per_coach": [{"coach_id": k, "replies": len(v), "median_reply_seconds": int(median(v))} for k, v in by_coach.items()],
    }


@router.post("/checkin/{athlete_id}", status_code=201)
def ask_coach_to_check_in(athlete_id: int, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Owner asks the coach to check in: opens a 'drift' flag the coach sees in the inbox and brief. Idempotent."""
    athlete = session.get(Athlete, athlete_id)
    if not athlete or athlete.gym_id != gym.id:
        raise HTTPException(404, "Athlete not found.")
    flag = session.exec(select(Flag).where(Flag.athlete_id == athlete.id, Flag.type == "drift", Flag.resolved_at == None)).first()
    if not flag:
        flag = Flag(athlete_id=athlete.id, type="drift", source="coach", detail="Owner asked for a check-in: quiet 10+ days")
        session.add(flag)
        session.commit()
        session.refresh(flag)
    return flag
