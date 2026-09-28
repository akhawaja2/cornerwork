"""SQLModel tables per docs/03-mvp-spec.md section 4. All datetimes are timezone-aware UTC."""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class Gym(SQLModel, table=True):
    __tablename__ = "gyms"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    twilio_number: Optional[str] = None
    timezone: str = "America/New_York"
    owner_email: Optional[str] = None
    api_token: Optional[str] = Field(default=None, unique=True, index=True)  # bearer token for the extension / magic link
    created_at: datetime = Field(default_factory=utcnow)


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    gym_id: int = Field(foreign_key="gyms.id")
    role: str  # owner | head_coach | coach
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None  # E.164
    created_at: datetime = Field(default_factory=utcnow)


class Athlete(SQLModel, table=True):
    __tablename__ = "athletes"
    __table_args__ = (UniqueConstraint("gym_id", "phone"), UniqueConstraint("gym_id", "gymdesk_member_id"))
    id: Optional[int] = Field(default=None, primary_key=True)
    gym_id: int = Field(foreign_key="gyms.id")
    name: str
    phone: Optional[str] = None  # E.164; null until the athlete texts JOIN or a roster supplies it
    gymdesk_member_id: Optional[str] = None
    status: str = "pending"  # pending | active | stopped
    coach_id: Optional[int] = Field(default=None, foreign_key="users.id")
    photo_path: Optional[str] = None
    membership_start: Optional[date] = None
    goal: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Consent(SQLModel, table=True):
    __tablename__ = "consents"
    id: Optional[int] = Field(default=None, primary_key=True)
    athlete_id: int = Field(foreign_key="athletes.id")
    action: str  # join | stop
    raw_message: str
    received_at: datetime = Field(default_factory=utcnow)
    twilio_sid: Optional[str] = None


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    gym_id: int = Field(foreign_key="gyms.id")
    athlete_id: Optional[int] = Field(default=None, foreign_key="athletes.id")
    direction: str  # in | out
    channel: str = "sms"  # sms | mms
    from_phone: str
    to_phone: str
    body: str = ""
    media_path: Optional[str] = None
    twilio_sid: Optional[str] = None
    received_at: datetime = Field(default_factory=utcnow)
    status: Optional[str] = None


class Log(SQLModel, table=True):
    __tablename__ = "logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    athlete_id: int = Field(foreign_key="athletes.id")
    message_id: Optional[int] = Field(default=None, foreign_key="messages.id")
    transcript: str
    summary: Optional[str] = None
    techniques: list = Field(default_factory=list, sa_column=Column(JSON))
    sentiment: Optional[str] = None  # pos | neutral | neg
    injury: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # {area, severity, quote}
    concussion_flag: bool = False
    coach_draft: Optional[str] = None
    llm_model: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Flag(SQLModel, table=True):
    __tablename__ = "flags"
    id: Optional[int] = Field(default=None, primary_key=True)
    athlete_id: int = Field(foreign_key="athletes.id")
    type: str  # injury | returning | new | fight_prep | drift
    source: str = "ai"  # ai | coach | system
    detail: Optional[str] = None
    opened_at: datetime = Field(default_factory=utcnow)
    resolved_at: Optional[datetime] = None


class Reply(SQLModel, table=True):
    __tablename__ = "replies"
    id: Optional[int] = Field(default=None, primary_key=True)
    log_id: int = Field(foreign_key="logs.id", unique=True)
    coach_id: Optional[int] = Field(default=None, foreign_key="users.id")
    body: str
    via: str = "web"  # web | sms
    message_id: Optional[int] = Field(default=None, foreign_key="messages.id")
    sent_at: Optional[datetime] = None  # null for migrated replies whose time is unknown
    reply_seconds: Optional[int] = None


class GymClass(SQLModel, table=True):
    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("gym_id", "name"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    gym_id: int = Field(foreign_key="gyms.id")
    name: str
    coach_id: Optional[int] = Field(default=None, foreign_key="users.id")
    weekday: Optional[int] = None  # 0 = Monday
    start_time: Optional[str] = None  # "HH:MM" gym-local
    duration_min: Optional[int] = None
    discipline: Optional[str] = None


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("class_id", "athlete_id", "class_date"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id")
    athlete_id: int = Field(foreign_key="athletes.id")
    class_date: date
    status: str  # booked | attended | no_show
    source: str = "manual"  # gymdesk | csv | manual | demo
    external_id: Optional[str] = None  # Gymdesk attendance row id


class Brief(SQLModel, table=True):
    __tablename__ = "briefs"
    id: Optional[int] = Field(default=None, primary_key=True)
    class_id: int = Field(foreign_key="classes.id")
    class_date: date
    generated_at: datetime = Field(default_factory=utcnow)
    content: dict = Field(default_factory=dict, sa_column=Column(JSON))
    sent_to_coach_at: Optional[datetime] = None


class Drill(SQLModel, table=True):
    __tablename__ = "drills"
    id: Optional[int] = Field(default=None, primary_key=True)
    gym_id: int = Field(foreign_key="gyms.id")
    coach_id: Optional[int] = Field(default=None, foreign_key="users.id")
    title: str
    url: Optional[str] = None
    tags: list = Field(default_factory=list, sa_column=Column(JSON))


class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: Optional[int] = Field(default=None, primary_key=True)
    gym_id: int = Field(foreign_key="gyms.id")
    athlete_id: Optional[int] = Field(default=None, foreign_key="athletes.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    type: str
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))
    at: datetime = Field(default_factory=utcnow)
