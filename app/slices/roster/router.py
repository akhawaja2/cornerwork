import re
from datetime import date, datetime, time, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import Session

from app.db import get_session
from app.deps import current_gym
from app.events import record
from app.models import Gym
from app.slices.roster.service import find_athlete, upsert_athlete, upsert_booking, upsert_class

router = APIRouter(prefix="/api/import")
E164 = r"^\+[1-9]\d{7,14}$"


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


@router.post("/attendance")
def import_attendance(snapshot: Snapshot, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Upsert one member's attendance. Re-posting the same snapshot creates nothing."""
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
    session.commit()
    return {"athlete_id": athlete.id, "records": len(snapshot.records), "created": created, "observed_at": snapshot.observedAt}


class RosterAthlete(BaseModel):
    name: str = Field(min_length=1)
    phone: str | None = Field(default=None, pattern=E164)
    gymdesk_member_id: str | None = Field(default=None, pattern=r"^\d+$")
    membership_start: date | None = None

    @model_validator(mode="after")
    def keyed(self):
        if not (self.phone or self.gymdesk_member_id):
            raise ValueError("phone or gymdesk_member_id is required")
        return self


class RosterBooking(BaseModel):
    class_name: str = Field(min_length=1)
    class_date: date
    status: Literal["booked", "attended", "no_show"]
    phone: str | None = Field(default=None, pattern=E164)
    gymdesk_member_id: str | None = Field(default=None, pattern=r"^\d+$")
    start_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    duration_min: int | None = Field(default=None, gt=0, le=1440)

    @model_validator(mode="after")
    def keyed(self):
        if not (self.phone or self.gymdesk_member_id):
            raise ValueError("phone or gymdesk_member_id is required")
        return self


class Roster(BaseModel):
    source: Literal["csv", "gymdesk", "manual"] = "csv"
    athletes: list[RosterAthlete] = Field(default_factory=list, max_length=1000)
    bookings: list[RosterBooking] = Field(default_factory=list, max_length=5000)


@router.post("/roster")
def import_roster(roster: Roster, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Athletes and bookings from a CSV export or the (future) Gymdesk roster reader. Imports never grant consent."""
    for a in roster.athletes:
        upsert_athlete(session, gym.id, a.name, gymdesk_member_id=a.gymdesk_member_id, phone=a.phone, membership_start=a.membership_start)
    created = 0
    for i, b in enumerate(roster.bookings):
        athlete = find_athlete(session, gym.id, gymdesk_member_id=b.gymdesk_member_id, phone=b.phone)
        if not athlete:
            raise HTTPException(422, f"bookings[{i}]: athlete not found; include them in athletes first.")
        cls = upsert_class(session, gym.id, b.class_name, b.start_time, b.duration_min, b.class_date.weekday())
        _, new = upsert_booking(session, cls.id, athlete.id, b.class_date, b.status, roster.source)
        if new:
            record(session, gym.id, "booking_imported", athlete_id=athlete.id,
                   meta={"class_id": cls.id, "date": b.class_date.isoformat(), "status": b.status, "source": roster.source})
            created += 1
    session.commit()
    return {"athletes": len(roster.athletes), "bookings": len(roster.bookings), "bookings_created": created,
            "note": "Imports do not grant consent."}
