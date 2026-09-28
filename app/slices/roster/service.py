"""Idempotent upserts. Athletes key on (gym_id, gymdesk_member_id) or (gym_id, phone);
classes on (gym_id, name); bookings on (class_id, athlete_id, class_date)."""
from sqlmodel import Session, select

from app.models import Athlete, Booking, GymClass


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
