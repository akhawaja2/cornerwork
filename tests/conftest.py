import os

os.environ["DEMO_MODE"] = "1"  # tests never call Anthropic, OpenAI or Twilio, whatever the shell has set
for _key in ("TWILIO_AUTH_TOKEN", "PUBLIC_URL"):
    os.environ.pop(_key, None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, select

from app import db
from app.events import record
from app.main import app
from app.models import Athlete, Gym, Log

# The real captured shape of Sarah Demo's attendance row (same fixture as extension-demo/test-gymdesk.cjs).
SNAPSHOT = {"memberId": "12672454", "memberName": "Sarah Demo", "gym": "AKLabs MMA", "observedAt": "2026-09-28T17:00:00Z",
            "records": [{"id": "62252846", "sessionId": "1832536", "date": "09/28/2026", "when": "Sep 28, 2026 7:00 AM",
                         "duration": "1h", "title": "Cornerwork Test — Boxing"}]}


@pytest.fixture
def client(tmp_path):
    db.init_db(tmp_path / "test.sqlite3")
    with Session(db.engine) as s:
        gym = s.exec(select(Gym)).first()
        gym.api_token = "test-token"
        s.add(gym)
        s.commit()
    c = TestClient(app, headers={"Authorization": "Bearer test-token"})  # no context manager: lifespan must not re-init with the env DB
    yield c
    c.close()


@pytest.fixture
def sarah_log(client):
    """Fixture shaped like the pilot's verified log. Not the user's Chrome data; that arrives via Phase 1.5 migration."""
    with Session(db.engine) as s:
        a = Athlete(gym_id=1, name="Sarah Demo", gymdesk_member_id="12672454", status="active")
        s.add(a)
        s.commit()
        s.refresh(a)
        log = Log(athlete_id=a.id, transcript="Class was OK, Abu is excellent")
        s.add(log)
        s.commit()
        s.refresh(log)
        record(s, 1, "log_received", athlete_id=a.id, meta={"log_id": log.id}, at=log.created_at)
        s.commit()
        return {"athlete_id": a.id, "log_id": log.id}
