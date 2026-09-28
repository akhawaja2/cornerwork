"""Idempotent upserts and the Gymdesk snapshot import.
Athletes key on (gym_id, gymdesk_member_id) or (gym_id, phone); classes on (gym_id, name);
bookings on (class_id, athlete_id, class_date)."""
import re
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.events import record
from app.models import Athlete, Booking, Gym, GymClass


class AttendanceRecord(BaseModel):
    """One row as gymdesk-reader.js captures it."""
    id: str = Field(pattern=r"^\d+$")
    sessionId: str = Field(pattern=r"^\d+$")
    title: str = Field(min_length=1)
    when: str  # "Sep 28, 2026 7:00 AM"
    duration: str  # "1h", "45m", "1.5h"
    date: str  # "MM/DD/YYYY"


class Snapshot(BaseModel):
    """The extension's gymdeskSnapshot, posted as-is."""
    memberId: str = Field(pattern=r"^\d+$")
    memberName: str = Field(min_length=1)
    gym: str
    observedAt: str | None = None
    records: list[AttendanceRecord] = Field(max_length=100)


def parse_record(r: AttendanceRecord):
    """Mirror core.js importGymdesk validation. Returns (class_date, 'HH:MM', minutes)."""
    try:
        class_date = datetime.strptime(r.date, "%m/%d/%Y").date()
    except ValueError:
        raise HTTPException(422, f"Invalid class date: {r.date}")
    clock = re.search(r"(\d{1,2}):(\d{2}) (AM|PM)$", r.when)
    dur = re.fullmatch(r"(?:(\d+(?:\.\d+)?)h)?\s*(?:(\d+)m)?", r.duration)
    if not clock or not 1 <= int(clock[1]) <= 12 or int(clock[2]) > 59 or not dur or not (dur[1] or dur[2]):
        raise HTTPException(422, f"Unsupported Gymdesk attendance format: {r.when} / {r.duration}")
    hour = int(clock[1]) % 12 + (12 if clock[3] == "PM" else 0)
    minutes = int(float(dur[1] or 0) * 60 + int(dur[2] or 0))
    if not 0 < minutes <= 1440:
        raise HTTPException(422, f"Invalid class duration: {r.duration}")
    return class_date, f"{hour:02d}:{clock[2]}", minutes


def find_athlete(session: Session, gym_id: int, gymdesk_member_id=None, phone=None) -> Athlete | None:
    query = select(Athlete).where(Athlete.gym_id == gym_id)
    query = query.where(Athlete.gymdesk_member_id == gymdesk_member_id) if gymdesk_member_id else query.where(Athlete.phone == phone)
    return session.exec(query).first()


def upsert_athlete(session: Session, gym_id: int, name: str, gymdesk_member_id=None, phone=None, membership_start=None) -> Athlete:
    athlete = find_athlete(session, gym_id, gymdesk_member_id, phone)
    if not athlete:
        athlete = Athlete(gym_id=gym_id, name=name)
        session.add(athlete)
    athlete.name = name or athlete.name
    athlete.gymdesk_member_id = gymdesk_member_id or athlete.gymdesk_member_id
    athlete.phone = phone or athlete.phone
    athlete.membership_start = membership_start or athlete.membership_start
    session.flush()
    return athlete


def upsert_class(session: Session, gym_id: int, name: str, start_time=None, duration_min=None, weekday=None) -> GymClass:
    cls = session.exec(select(GymClass).where(GymClass.gym_id == gym_id, GymClass.name == name)).first()
    if not cls:
        cls = GymClass(gym_id=gym_id, name=name)
        session.add(cls)
    cls.start_time = start_time or cls.start_time
    cls.duration_min = duration_min or cls.duration_min
    cls.weekday = weekday if weekday is not None else cls.weekday
    session.flush()
    return cls


def upsert_booking(session: Session, class_id: int, athlete_id: int, class_date, status: str, source: str, external_id=None):
    """Returns (booking, created)."""
    booking = session.exec(select(Booking).where(
        Booking.class_id == class_id, Booking.athlete_id == athlete_id, Booking.class_date == class_date)).first()
    created = booking is None
    if created:
        booking = Booking(class_id=class_id, athlete_id=athlete_id, class_date=class_date, status=status, source=source)
        session.add(booking)
    booking.status, booking.source = status, source
    booking.external_id = external_id or booking.external_id
    session.flush()
    return booking, created


def import_snapshot(session: Session, gym: Gym, snapshot: Snapshot) -> dict:
    """Upsert one member's attendance. Re-posting the same snapshot creates nothing. Caller commits."""
    if snapshot.gym != gym.name:
        raise HTTPException(400, f"Snapshot is for '{snapshot.gym}'; this backend is '{gym.name}'.")
    athlete = upsert_athlete(session, gym.id, snapshot.memberName, gymdesk_member_id=snapshot.memberId)
    created = 0
    for r in snapshot.records:
        class_date, start, minutes = parse_record(r)
        cls = upsert_class(session, gym.id, r.title, start, minutes, class_date.weekday())
        _, new = upsert_booking(session, cls.id, athlete.id, class_date, "attended", "gymdesk", external_id=r.id)
        if new:
            local = datetime.combine(class_date, time.fromisoformat(start), tzinfo=ZoneInfo(gym.timezone))
            record(session, gym.id, "check_in", athlete_id=athlete.id, at=local.astimezone(timezone.utc),
                   meta={"class_id": cls.id, "date": class_date.isoformat(), "gymdesk_row_id": r.id, "gymdesk_session_id": r.sessionId})
            created += 1
    return {"athlete_id": athlete.id, "records": len(snapshot.records), "created": created, "observed_at": snapshot.observedAt}
