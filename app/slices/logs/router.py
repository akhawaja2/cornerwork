from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.models import Athlete, Gym, Log, Reply

router = APIRouter(prefix="/api")


@router.get("/inbox")
def inbox(session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Logs newest-first with athlete and reply (null when unanswered)."""
    rows = session.exec(
        select(Log, Athlete).join(Athlete).where(Athlete.gym_id == gym.id).order_by(Log.created_at.desc(), Log.id.desc())
    ).all()
    replies = {r.log_id: r for r in session.exec(select(Reply).where(Reply.log_id.in_([log.id for log, _ in rows]))).all()} if rows else {}
    return {
        "logs": [
            {**log.model_dump(), "athlete": {"id": a.id, "name": a.name, "status": a.status}, "reply": replies.get(log.id)}
            for log, a in rows
        ]
    }
