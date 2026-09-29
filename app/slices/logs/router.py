from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.models import Athlete, Gym, Log, Reply

router = APIRouter(prefix="/api")


@router.get("/inbox")
def inbox(member: str | None = Query(default=None, pattern=r"^\d+$"), athlete: int | None = Query(default=None, gt=0),
          session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    """Logs newest-first with athlete and reply (null when unanswered).
    ?athlete=<id> or ?member=<gymdesk member id> scopes to one athlete and adds "athlete" (null when unknown)."""
    query = select(Log, Athlete).join(Athlete).where(Athlete.gym_id == gym.id)
    scoped = {}
    if member or athlete:
        who = session.exec(select(Athlete).where(Athlete.gym_id == gym.id, Athlete.gymdesk_member_id == member)).first() if member \
            else session.exec(select(Athlete).where(Athlete.gym_id == gym.id, Athlete.id == athlete)).first()
        scoped = {"athlete": {"id": who.id, "name": who.name, "status": who.status} if who else None}
        query = query.where(Athlete.id == (who.id if who else -1))
    rows = session.exec(query.order_by(Log.created_at.desc(), Log.id.desc())).all()
    replies = {r.log_id: r for r in session.exec(select(Reply).where(Reply.log_id.in_([log.id for log, _ in rows]))).all()} if rows else {}
    return {
        "logs": [
            {**log.model_dump(), "athlete": {"id": a.id, "name": a.name, "status": a.status}, "reply": replies.get(log.id)}
            for log, a in rows
        ],
        **scoped,
    }
