"""Engine + session. CORNERWORK_DB selects the SQLite file; one gym row is seeded (CORNERWORK_GYM)."""
import os

import app.config  # noqa: F401  loads .env first
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Gym

engine = None


def init_db(path=None):
    global engine
    path = Path(path or os.environ.get("CORNERWORK_DB", "data/cornerwork.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path.as_posix()}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.exec(select(Gym)).first():
            session.add(Gym(name=os.environ.get("CORNERWORK_GYM", "AKLabs MMA")))
            session.commit()
    return engine


def get_session():
    with Session(engine) as session:
        yield session
