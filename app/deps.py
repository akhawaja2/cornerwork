"""Request dependencies. Phase 1.3 replaces current_gym with bearer-token lookup."""
from fastapi import Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Gym


def current_gym(session: Session = Depends(get_session)) -> Gym:
    # ponytail: single seeded gym until Phase 1.3 issues per-gym tokens
    return session.exec(select(Gym).order_by(Gym.id)).first()
