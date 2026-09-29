from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.events import record
from app.models import Athlete, Flag, Gym, Log, utcnow
from app.slices.roster.service import Snapshot, find_athlete, import_snapshot, upsert_athlete, upsert_booking, upsert_class

router = APIRouter(prefix="/api")
E164 = r"^\+[1-9]\d{7,14}$"


@router.get("/athletes")
def list_athletes(session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Roster with last log time, 7-day log count and open flags. Phone shown as last 4 digits only."""
    week = utcnow() - timedelta(days=7)
    out = []
    for a in session.exec(select(Athlete).where(Athlete.gym_id == gym.id).order_by(Athlete.name)).all():
        logs = session.exec(select(Log.created_at).where(Log.athlete_id == a.id).order_by(Log.created_at.desc())).all()
        flags = session.exec(select(Flag).where(Flag.athlete_id == a.id, Flag.resolved_at == None)).all()
        out.append({"id": a.id, "name": a.name, "status": a.status, "goal": a.goal, "gymdesk_member_id": a.gymdesk_member_id,
                    "phone_last4": a.phone[-4:] if a.phone else None, "membership_start": a.membership_start,
                    "last_log_at": logs[0] if logs else None, "logs_7d": sum(t >= week for t in logs), "logs_total": len(logs),
                    "flags": [{"type": f.type, "detail": f.detail} for f in flags]})
    return out


@router.post("/import/attendance")
def import_attendance(snapshot: Snapshot, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Upsert one member's attendance from the extension's gymdeskSnapshot. Idempotent."""
    result = import_snapshot(session, gym, snapshot)
    session.commit()
    return result


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


@router.post("/import/roster")
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
