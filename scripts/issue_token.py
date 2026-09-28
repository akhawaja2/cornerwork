"""Print the gym API token; create it if missing. --rotate replaces it.
Usage: .venv/Scripts/python.exe scripts/issue_token.py [--rotate]"""
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlmodel import Session, select  # noqa: E402

from app.db import init_db  # noqa: E402
from app.models import Gym  # noqa: E402

with Session(init_db()) as session:
    gym = session.exec(select(Gym).order_by(Gym.id)).first()
    if not gym.api_token or "--rotate" in sys.argv:
        gym.api_token = secrets.token_urlsafe(32)
        session.add(gym)
        session.commit()
    print(gym.api_token)
