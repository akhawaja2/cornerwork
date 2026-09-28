from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.events import record
from app.integrations.llm import edit_distance
from app.integrations.twilio_client import send_sms
from app.models import Athlete, Gym, Log, Reply, utcnow
from app.slices.inbound.router import coach_name

router = APIRouter(prefix="/api")


class ReplyIn(BaseModel):
    log_id: int = Field(gt=0)
    body: str = Field(min_length=1, max_length=1600)
    coach_id: int | None = None


@router.post("/replies", status_code=201)
def create_reply(payload: ReplyIn, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Stores the coach reply and the reply_sent event. Outbound SMS arrives in Phase 4."""
    log = session.get(Log, payload.log_id)
    athlete = log and session.get(Athlete, log.athlete_id)
    if not log or athlete.gym_id != gym.id:
        raise HTTPException(404, "Log not found.")
    if session.exec(select(Reply).where(Reply.log_id == log.id)).first():
        raise HTTPException(409, "This log already has a reply.")
    body = payload.body.strip()
    if not body:
        raise HTTPException(422, "Write a reply first.")
    sent = utcnow()
    seconds = max(0, int((sent - log.created_at).total_seconds()))
    reply = Reply(log_id=log.id, coach_id=payload.coach_id, body=body, via="web", sent_at=sent, reply_seconds=seconds)
    if athlete.phone and athlete.status == "active":  # consent gate: stopped/pending athletes get no text
        reply.message_id = send_sms(session, gym, athlete, f"{coach_name()}: {body}").id
    session.add(reply)
    meta = {"log_id": log.id, "reply_seconds": seconds, "via": "web"}
    if log.coach_draft:  # the pilot's key moat metric: how much the coach changed the AI draft
        meta |= {"edit_distance": edit_distance(log.coach_draft, body), "draft_len": len(log.coach_draft)}
    record(session, gym.id, "reply_sent", athlete_id=athlete.id, user_id=payload.coach_id, meta=meta, at=sent)
    session.commit()
    session.refresh(reply)
    return reply
