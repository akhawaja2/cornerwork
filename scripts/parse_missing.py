"""Parse logs stored before the parser existed (llm_model is null), e.g. the migrated Chrome log.
Usage: .venv/Scripts/python.exe scripts/parse_missing.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlmodel import Session, select  # noqa: E402

from app.db import init_db  # noqa: E402
from app.integrations.llm import get_llm  # noqa: E402
from app.models import Athlete, Gym, Log  # noqa: E402
from app.slices.logs.service import parse_log  # noqa: E402

with Session(init_db()) as session:
    gym = session.exec(select(Gym).order_by(Gym.id)).first()
    todo = session.exec(select(Log).where(Log.llm_model == None)).all()
    done = sum(parse_log(session, gym, session.get(Athlete, log.athlete_id), log) for log in todo)
    session.commit()
    print(f"{get_llm().model}: parsed {done} of {len(todo)} unparsed logs")
