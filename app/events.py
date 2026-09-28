"""Every metric comes from the events table. docs/08-agent-handoff.md section 10 fixes the type list."""
from app.models import Event, utcnow

TYPES = {
    "opt_in", "opt_out", "log_received", "log_parsed", "injury_flagged", "reply_sent", "reply_read",
    "nudge_sent", "recap_sent", "brief_generated", "brief_opened", "booking_imported", "check_in",
}


def record(session, gym_id, type, athlete_id=None, user_id=None, meta=None, at=None) -> Event:
    if type not in TYPES:
        raise ValueError(f"Unknown event type: {type}")
    event = Event(gym_id=gym_id, athlete_id=athlete_id, user_id=user_id, type=type, meta=meta or {}, at=at or utcnow())
    session.add(event)
    return event
