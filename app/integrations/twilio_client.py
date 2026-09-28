"""Twilio boundary: outbound SMS, media download, webhook signature check. Stdlib + httpx, no twilio package.
Fake mode (DEMO_MODE=1 or missing TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_NUMBER): nothing leaves the machine;
outbound messages are stored with status 'simulated'."""
import base64
import hashlib
import hmac
import logging
import os

import httpx
from sqlmodel import Session

from app.models import Athlete, Gym, Message

logger = logging.getLogger(__name__)


def creds():
    sid, token, number = os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"), os.environ.get("TWILIO_NUMBER")
    if os.environ.get("DEMO_MODE") == "1" or not (sid and token and number):
        return None
    return sid, token, number


def send_sms(session: Session, gym: Gym, athlete: Athlete, body: str) -> Message:
    """Stores an outbound Message row and, when credentials exist, sends it. Caller commits.
    Never call for a stopped athlete; the caller checks consent."""
    c = creds()
    msg = Message(gym_id=gym.id, athlete_id=athlete.id, direction="out", channel="sms",
                  from_phone=(c[2] if c else gym.twilio_number or "+10000000000"), to_phone=athlete.phone, body=body[:1600], status="simulated")
    if c:
        sid, token, number = c
        r = httpx.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", auth=(sid, token),
                       data={"From": number, "To": athlete.phone, "Body": body[:1600]}, timeout=20)
        if r.status_code >= 300:
            logger.error("Twilio send failed %s: %s", r.status_code, r.text[:200])
            msg.status = f"failed:{r.status_code}"
        else:
            data = r.json()
            msg.twilio_sid, msg.status = data.get("sid"), data.get("status", "queued")
    session.add(msg)
    session.flush()
    return msg


def fetch_media(url: str) -> bytes:
    c = creds()
    if not c:
        return b""  # fake mode: the transcriber ignores the bytes
    r = httpx.get(url, auth=(c[0], c[1]), follow_redirects=True, timeout=30)
    r.raise_for_status()
    return r.content


def signature(url: str, params: dict, auth_token: str) -> str:
    """Twilio request signature: base64(HMAC-SHA1(token, url + sorted key+value pairs))."""
    payload = url + "".join(k + params[k] for k in sorted(params))
    return base64.b64encode(hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()).decode()


def valid_signature(url: str, params: dict, header: str | None) -> bool:
    """True when no auth token is configured (local dev, logged), else constant-time compare."""
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not token:
        logger.warning("TWILIO_AUTH_TOKEN not set: accepting /sms without signature check")
        return True
    return bool(header) and hmac.compare_digest(signature(url, params, token), header)
