import logging
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.events import record
from app.integrations.llm import get_llm
from app.models import Athlete, Booking, Brief, Event, Flag, Gym, GymClass, Log, utcnow

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)
RETURNING_GAP_DAYS = 21


def next_date_for(session: Session, cls: GymClass, today: date) -> date | None:
    """Next date with a booking, else the next weekday occurrence if the class has one."""
    booked = session.exec(select(Booking.class_date).where(Booking.class_id == cls.id, Booking.class_date >= today)
                          .order_by(Booking.class_date).limit(1)).first()
    if booked:
        return booked
    if cls.weekday is None:
        return None
    return today + timedelta(days=(cls.weekday - today.weekday()) % 7)


@router.get("/classes")
def classes(session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Classes with their next date, soonest first."""
    today = datetime.now(timezone.utc).date()
    rows = session.exec(select(GymClass).where(GymClass.gym_id == gym.id)).all()
    out = [{**c.model_dump(), "next_date": (d := next_date_for(session, c, today)) and d.isoformat()} for c in rows]
    return sorted(out, key=lambda c: (c["next_date"] or "9999", c["start_time"] or "", c["name"]))


@router.get("/brief/{class_id}/{class_date}")
def brief(class_id: int, class_date: date, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Pre-class brief: who is on the mat with flags and a one-liner, counts, last-7-day themes, focus + notes.
    Focus/notes come from the LLM (or the deterministic fake) and are cached in `briefs` until newer logs appear."""
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
    themes, athletes, newest = Counter(), [], None
    for booking, a in rows:
        flags = [{"type": f.type, "source": f.source, "detail": f.detail}
                 for f in session.exec(select(Flag).where(Flag.athlete_id == a.id, Flag.resolved_at == None)).all()]
        if a.membership_start and 0 <= (class_date - a.membership_start).days <= 14:
            flags.append({"type": "new", "source": "system", "detail": "Joined within two weeks"})
        last_checkin = session.exec(select(Event.at).where(Event.athlete_id == a.id, Event.type == "check_in", Event.at < since + timedelta(days=7))
                                    .order_by(Event.at.desc()).limit(1)).first()
        if last_checkin and (class_date - last_checkin.date()).days > RETURNING_GAP_DAYS:
            flags.append({"type": "returning", "source": "system", "detail": f"First class back after {(class_date - last_checkin.date()).days} days"})
        logs = session.exec(select(Log).where(Log.athlete_id == a.id, Log.created_at >= since, Log.created_at <= until)
                            .order_by(Log.created_at.desc())).all()
        for log in logs:
            themes.update(log.techniques or [])
        if logs:
            newest = max(newest or logs[0].created_at, logs[0].created_at)
        athletes.append({"id": a.id, "name": a.name, "status": a.status, "goal": a.goal, "booking_status": booking.status, "source": booking.source,
                         "flags": flags, "log_count_7d": len(logs),
                         "latest_summary": (logs[0].summary or logs[0].transcript) if logs else None,
                         "summaries": [log.summary or log.transcript for log in logs[:3]]})
    theme_list = [{"name": k, "count": v} for k, v in themes.most_common(5)]
    llm = get_llm()
    cached = session.exec(select(Brief).where(Brief.class_id == class_id, Brief.class_date == class_date)).first()
    fresh = cached and cached.content.get("model") == llm.model and cached.content.get("athlete_count") == len(athletes) \
        and (newest is None or cached.generated_at >= newest)
    if fresh:
        generated = cached.content
    else:
        try:
            out = llm.build_brief(class_info["name"], class_date.isoformat(), athletes, theme_list)
            generated = {"focus": out.focus, "notes": [n.model_dump() for n in out.notes], "model": llm.model, "athlete_count": len(athletes)}
        except Exception as e:  # keep the page working; deterministic fallback, not cached
            logger.warning("build_brief failed: %s", e)
            generated = {"focus": "Check in individually before class; ask what each athlete wants to work on.",
                         "notes": [], "model": "fallback", "athlete_count": len(athletes)}
        if generated["model"] != "fallback":
            if cached:
                cached.content, cached.generated_at = generated, utcnow()
                session.add(cached)
            else:
                session.add(Brief(class_id=class_id, class_date=class_date, content=generated))
            record(session, gym.id, "brief_generated", meta={"class_id": class_id, "date": class_date.isoformat(), "model": llm.model})
    notes = {n["athlete"]: n["note"] for n in generated.get("notes", [])}
    for a in athletes:
        a["note"] = notes.get(a["name"]) or (a["flags"][0]["detail"] if a["flags"] else None) or a["latest_summary"]
    flag_counts = Counter(f["type"] for a in athletes for f in a["flags"])
    record(session, gym.id, "brief_opened", meta={"class_id": class_id, "date": class_date.isoformat()})
    session.commit()
    return {"class": class_info, "date": class_date, "athletes": athletes, "themes": theme_list,
            "counts": {"registered": len(athletes), "coached": sum(a["status"] == "active" for a in athletes),
                       "new": flag_counts.get("new", 0), "flagged": sum(bool(a["flags"]) for a in athletes),
                       "flags": dict(flag_counts)},
            "focus": generated["focus"], "notes": generated["notes"],
            "sources": sorted({b.source for b, _ in rows}), "generator": generated["model"]}
