import json
from pathlib import Path

from sqlmodel import Session

from app import db
from app.deps import gym_for_token
from scripts.migrate_chrome_state import coaching_state, migrate

BACKUP = Path(__file__).resolve().parents[1] / "backup" / "chrome-localstorage-2026-09-28.json"


def test_migrate_installed_backup_is_idempotent(client):
    """Runs against the real exported backup, twice."""
    state = coaching_state(json.loads(BACKUP.read_text(encoding="utf-8")))
    with Session(db.engine) as s:
        gym = gym_for_token(s, "test-token")
        first = migrate(s, gym, state)
        second = migrate(s, gym, state)
    assert first["logs"] == 1 and first["replies"] == 1 and first["attendance"]["created"] == 1
    assert second == {**first, "logs": 0, "replies": 0, "skipped": 1, "attendance": {**first["attendance"], "created": 0}}
    logs = client.get("/api/inbox").json()["logs"]
    assert len(logs) == 1
    assert logs[0]["transcript"] == "Class was OK, Abu is excellent" and logs[0]["reply"]["body"] == "Thanks!"
    assert logs[0]["reply"]["reply_seconds"] is None and logs[0]["created_at"].startswith("2026-09-28T19:24:07")
    summary = client.get("/api/owner/summary").json()
    assert summary["total_logs"] == 1 and summary["total_replies"] == 1 and summary["median_reply_seconds"] is None
    assert client.get("/api/brief/1/2026-09-28").json()["athletes"][0]["latest_summary"] == "Class was OK, Abu is excellent"
