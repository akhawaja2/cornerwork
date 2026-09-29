"""Twilio webhook: POST /sms (form-encoded). JOIN/STOP consent, text or voice-note log intake, TwiML acks.
Replies to the athlete go back inline as TwiML so no second API call is needed."""
import logging
import os
from pathlib import Path
from urllib.parse import parse_qs
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlmodel import Session, select

from app.db import get_session
from app.events import record
from app.integrations.transcribe import transcribe
from app.integrations.twilio_client import fetch_media, valid_signature
from app.models import Athlete, Consent, Gym, Message, utcnow
from app.slices.logs.service import create_log

router = APIRouter()
logger = logging.getLogger(__name__)
MEDIA_DIR = Path(os.environ.get("CORNERWORK_MEDIA", "data/media"))
STOP_WORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}
JOIN_WORDS = {"JOIN", "START", "UNSTOP"}


def coach_name() -> str:
    return os.environ.get("COACH_NAME", "Your coach")


def consent_text(gym: Gym) -> str:
    return (f"{gym.name} coaching texts via Cornerwork. Reply YES 18 to confirm you are 18 or older and agree to receive "
            f"coaching messages after class. Reply STOP anytime. Msg & data rates may apply.")


def twiml(text: str | None) -> Response:
    body = '<?xml version="1.0" encoding="UTF-8"?><Response>' + (f"<Message>{escape(text)}</Message>" if text else "") + "</Response>"
    return Response(body, media_type="application/xml")


def reply(session: Session, gym: Gym, athlete: Athlete, text: str) -> Response:
    """Record the outbound message (delivered by Twilio from the TwiML) and answer."""
    session.add(Message(gym_id=gym.id, athlete_id=athlete.id, direction="out", channel="sms",
                        from_phone=gym.twilio_number or os.environ.get("TWILIO_NUMBER", ""), to_phone=athlete.phone, body=text, status="twiml"))
    session.commit()
    return twiml(text)


@router.post("/sms")
async def inbound_sms(request: Request, session: Session = Depends(get_session)):
    raw = (await request.body()).decode("utf-8", "replace")
    params = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
    url = os.environ.get("PUBLIC_URL", str(request.base_url).rstrip("/")) + "/sms"
    if not valid_signature(url, params, request.headers.get("X-Twilio-Signature")):
        raise HTTPException(403, "Bad Twilio signature.")
    from_phone, to_phone = params.get("From", "").strip(), params.get("To", "").strip()
    if not from_phone.startswith("+"):
        raise HTTPException(422, "From must be E.164.")
    gym = session.exec(select(Gym).where(Gym.twilio_number == to_phone)).first() or session.exec(select(Gym).order_by(Gym.id)).first()
    athlete = session.exec(select(Athlete).where(Athlete.gym_id == gym.id, Athlete.phone == from_phone)).first()
    if not athlete:
        athlete = Athlete(gym_id=gym.id, name=from_phone, phone=from_phone, status="pending")
        session.add(athlete)
        session.flush()
    body = params.get("Body", "").strip()
    media_count = int(params.get("NumMedia", "0") or 0)
    inbound = Message(gym_id=gym.id, athlete_id=athlete.id, direction="in", channel="mms" if media_count else "sms",
                      from_phone=from_phone, to_phone=to_phone, body=body, twilio_sid=params.get("MessageSid"), status="received")
    session.add(inbound)
    session.flush()
    command = body.upper()

    if command in STOP_WORDS:
        athlete.status = "stopped"
        session.add(Consent(athlete_id=athlete.id, action="stop", raw_message=body, twilio_sid=inbound.twilio_sid))
        record(session, gym.id, "opt_out", athlete_id=athlete.id, meta={"message_id": inbound.id})
        return reply(session, gym, athlete, "You are opted out of Cornerwork coaching texts. Text JOIN to restart.")
    if command in JOIN_WORDS:
        if athlete.status == "active":
            return reply(session, gym, athlete, "You are already opted in. Text after class and your coach will reply.")
        athlete.status = "pending"
        session.add(Consent(athlete_id=athlete.id, action="join_requested", raw_message=body, twilio_sid=inbound.twilio_sid))
        return reply(session, gym, athlete, consent_text(gym))
    if command.startswith("YES") and athlete.status == "pending":
        asked = session.exec(select(Consent).where(Consent.athlete_id == athlete.id, Consent.action == "join_requested")).first()
        if not asked:
            return reply(session, gym, athlete, f"Text JOIN first to see the consent terms for {gym.name}.")
        if "18" not in command:
            return reply(session, gym, athlete, "Reply YES 18 to confirm you are 18 or older.")
        athlete.status = "active"
        session.add(Consent(athlete_id=athlete.id, action="join", raw_message=body + " | " + consent_text(gym), twilio_sid=inbound.twilio_sid))
        record(session, gym.id, "opt_in", athlete_id=athlete.id, meta={"message_id": inbound.id})
        return reply(session, gym, athlete, f"You are in. After class, text or voice-note what clicked and anything sore. {coach_name()} will reply. STOP anytime.")
    if athlete.status == "stopped":
        session.commit()
        return twiml(None)  # STOP is honoured: no outbound text at all
    if athlete.status != "active":
        return reply(session, gym, athlete, f"Text JOIN to get coaching texts from {gym.name} (adults only).")

    transcript, source = body, "sms"
    if media_count and params.get("MediaContentType0", "").startswith("audio/"):
        content_type = params["MediaContentType0"]
        audio = fetch_media(params.get("MediaUrl0", ""))
        ext = content_type.split("/")[1].split(";")[0]
        filename = f"{inbound.twilio_sid or inbound.id}.{ext}"
        if audio:
            MEDIA_DIR.mkdir(parents=True, exist_ok=True)
            (MEDIA_DIR / filename).write_bytes(audio)
            inbound.media_path = str(MEDIA_DIR / filename)
        text, model = transcribe(audio, filename, content_type)
        transcript, source = (text + ("\n" + body if body else "")), f"mms:{model}"
    if not transcript.strip():
        return reply(session, gym, athlete, "Send a short text or a voice note about class and your coach will reply.")
    log = create_log(session, gym, athlete, transcript, message_id=inbound.id, source=source)
    ack = f"Logged: {log.summary} I've let {coach_name()} know." if log.summary and log.summary != log.transcript \
        else f"Got it. {coach_name()} will reply."
    if log.concussion_flag:
        ack += " You mentioned a possible head knock: please get checked by a medical professional before training again. This service cannot assess injuries."
    elif log.injury:
        ack += f" Flagged the {log.injury.get('area', 'injury')} to your coach. If it is serious, please see a medical professional."
    return reply(session, gym, athlete, ack)
