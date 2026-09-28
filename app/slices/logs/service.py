"""Log intake: store, parse with the LLM (or the deterministic fake), flag injuries, record events."""
import logging

from sqlmodel import Session, select

from app.events import record
from app.integrations.llm import get_llm, safety_check
from app.models import Athlete, Flag, Gym, Log, utcnow

logger = logging.getLogger(__name__)


def create_log(session: Session, gym: Gym, athlete: Athlete, transcript: str, created_at=None, message_id=None, source="sms") -> Log:
    """Caller commits. Parsing failure never loses the log: it stays unparsed with llm_model=None."""
    log = Log(athlete_id=athlete.id, transcript=transcript, message_id=message_id, created_at=created_at or utcnow())
    session.add(log)
    session.flush()
    record(session, gym.id, "log_received", athlete_id=athlete.id, meta={"log_id": log.id, "source": source}, at=log.created_at)
    parse_log(session, gym, athlete, log)
    return log


def parse_log(session: Session, gym: Gym, athlete: Athlete, log: Log) -> bool:
    earlier = session.exec(select(Log).where(Log.athlete_id == athlete.id, Log.id != log.id, Log.summary != None)
                           .order_by(Log.created_at.desc()).limit(3)).all()
    llm = get_llm()
    try:
        parsed = llm.parse_log(log.transcript, athlete.goal or "", [e.summary for e in earlier])
    except Exception as e:  # network, schema after retry, rate limit: keep the raw log, coach still sees it
        logger.warning("parse_log failed for log %s: %s", log.id, e)
        return False
    parsed = safety_check(log.transcript, parsed)
    log.summary, log.techniques, log.sentiment = parsed.summary, parsed.techniques, parsed.sentiment
    log.injury = parsed.injury.model_dump() if parsed.injury else None
    log.concussion_flag, log.coach_draft, log.llm_model = parsed.concussion_flag, parsed.coach_draft, llm.model
    record(session, gym.id, "log_parsed", athlete_id=athlete.id, at=log.created_at,
           meta={"log_id": log.id, "model": llm.model, "sentiment": parsed.sentiment, "techniques": parsed.techniques})
    if parsed.injury or parsed.concussion_flag:
        detail = "Possible head injury: " + (parsed.injury.quote if parsed.injury else log.transcript[:120]) if parsed.concussion_flag \
            else f"{parsed.injury.area} ({parsed.injury.severity}): {parsed.injury.quote}"
        session.add(Flag(athlete_id=athlete.id, type="injury", source="ai", detail=detail, opened_at=log.created_at))
        record(session, gym.id, "injury_flagged", athlete_id=athlete.id, at=log.created_at,
               meta={"log_id": log.id, "area": parsed.injury.area if parsed.injury else None,
                     "severity": parsed.injury.severity if parsed.injury else None, "concussion": parsed.concussion_flag})
    return True
