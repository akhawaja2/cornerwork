"""Request dependencies: bearer-token -> Gym. Token issued by scripts/issue_token.py."""
from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Gym


def gym_for_token(session: Session, token: str | None) -> Gym | None:
    return session.exec(select(Gym).where(Gym.api_token == token)).first() if token else None


def current_gym(session: Session = Depends(get_session), authorization: str | None = Header(default=None)) -> Gym:
    token = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else None
    gym = gym_for_token(session, token)
    if not gym:
        raise HTTPException(401, "Missing or invalid bearer token.", headers={"WWW-Authenticate": "Bearer"})
    return gym
