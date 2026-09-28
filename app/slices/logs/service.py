"""Log intake. Every log gets a log_received event. Phase 3 adds parse_log here."""
from sqlmodel import Session

from app.events import record
from app.models import Athlete, Gym, Log, utcnow


def create_log(session: Session, gym: Gym, athlete: Athlete, transcript: str, created_at=None, message_id=None, source="sms") -> Log:
    """Caller commits."""
    log = Log(athlete_id=athlete.id, transcript=transcript, message_id=message_id, created_at=created_at or utcnow())
    session.add(log)
    session.flush()
    record(session, gym.id, "log_received", athlete_id=athlete.id, meta={"log_id": log.id, "source": source}, at=log.created_at)
    return log
