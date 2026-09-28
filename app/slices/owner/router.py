from datetime import datetime, time, timedelta, timezone
from statistics import median

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.models import Athlete, Event, Gym, utcnow

router = APIRouter(prefix="/api/owner")


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
    secs = [e.meta.get("reply_seconds", 0) for e in replies]
    weekly_loggers = {e.athlete_id for e in logs if e.at >= week} & active
    last_activity = {}
    for e in events:
        if e.type in ("log_received", "check_in") and e.athlete_id:
            last_activity[e.athlete_id] = max(e.at, last_activity.get(e.athlete_id, e.at))
    drift = []
    for a in athletes:
        if a.id not in active:
            continue
        last = last_activity.get(a.id) or datetime.combine(a.membership_start or a.created_at.date(), time(), tzinfo=timezone.utc)
        if (now - last).days >= 10:
            drift.append({"id": a.id, "name": a.name, "days_inactive": (now - last).days, "last_activity": last})
    by_coach = {}
    for e in replies:
        by_coach.setdefault(e.user_id, []).append(e.meta.get("reply_seconds", 0))
    return {
        "period_days": 7, "computed_from": "events",
        "roster": len(athletes), "coached": len(active),
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
