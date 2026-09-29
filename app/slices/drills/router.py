from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.deps import current_gym
from app.models import Drill, Gym

router = APIRouter(prefix="/api/drills")


class DrillIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    url: str | None = Field(default=None, max_length=500, pattern=r"^https?://")
    tags: list[str] = Field(default_factory=list, max_length=10)


@router.get("")
def list_drills(session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    return session.exec(select(Drill).where(Drill.gym_id == gym.id).order_by(Drill.title)).all()


@router.post("", status_code=201)
def create_drill(payload: DrillIn, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    drill = Drill(gym_id=gym.id, title=payload.title.strip(), url=payload.url, tags=[t.strip().lower() for t in payload.tags if t.strip()])
    session.add(drill)
    session.commit()
    session.refresh(drill)
    return drill


@router.delete("/{drill_id}", status_code=204)
def delete_drill(drill_id: int, session: Session = Depends(get_session), gym: Gym = Depends(current_gym)):
    drill = session.get(Drill, drill_id)
    if not drill or drill.gym_id != gym.id:
        raise HTTPException(404, "Drill not found.")
    session.delete(drill)
    session.commit()
