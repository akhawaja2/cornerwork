from collections import Counter
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.events import record
from app.models import Athlete, Booking, Flag, Gym, GymClass, Log

router = APIRouter(prefix="/api")


@router.get("/classes")
def classes(session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    return session.exec(select(GymClass).where(GymClass.gym_id == gym.id).order_by(GymClass.name)).all()


@router.get("/brief/{class_id}/{class_date}")
def brief(class_id: int, class_date: date, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Pre-class brief: booked/attended athletes, open flags, last-7-day themes, one focus line.
    Deterministic rules; Phase 3.3 swaps in the LLM generator."""
    cls = session.get(GymClass, class_id)
    if not cls or cls.gym_id != gym.id:
        raise HTTPException(404, "Class not found.")
    class_info = cls.model_dump()  # before commit expires the instance
    rows = session.exec(
        select(Booking, Athlete).join(Athlete).where(
            Booking.class_id == class_id, Booking.class_date == class_date, Booking.status.in_(["booked", "attended"])
        )
    ).all()
    since = datetime.combine(class_date, time(), tzinfo=timezone.utc) - timedelta(days=7)
    until = datetime.combine(class_date, time.max, tzinfo=timezone.utc)
    themes, athletes = Counter(), []
    for booking, a in rows:
        flags = [{"type": f.type, "source": f.source, "detail": f.detail}
                 for f in session.exec(select(Flag).where(Flag.athlete_id == a.id, Flag.resolved_at == None)).all()]
        if a.membership_start and 0 <= (class_date - a.membership_start).days <= 14:
            flags.append({"type": "new", "source": "system", "detail": "Joined within two weeks"})
        logs = session.exec(select(Log).where(Log.athlete_id == a.id, Log.created_at >= since, Log.created_at <= until)
                            .order_by(Log.created_at.desc())).all()
        for log in logs:
            themes.update(log.techniques or [])
        athletes.append({"id": a.id, "name": a.name, "status": a.status, "booking_status": booking.status, "source": booking.source,
                         "flags": flags, "log_count_7d": len(logs),
                         "latest_summary": (logs[0].summary or logs[0].transcript) if logs else None})
    focus = (f"Revisit {themes.most_common(1)[0][0]} with the group; check flags first." if themes
             else "Check in individually before class; ask what each athlete wants to work on.")
    record(session, gym.id, "brief_opened", meta={"class_id": class_id, "date": class_date.isoformat()})
    session.commit()
    return {"class": class_info, "date": class_date, "athletes": athletes,
            "themes": [{"name": k, "count": v} for k, v in themes.most_common(5)], "focus": focus,
            "sources": sorted({b.source for b, _ in rows}), "generator": "deterministic rules"}
