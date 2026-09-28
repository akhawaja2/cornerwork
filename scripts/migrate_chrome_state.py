"""One-time import of the installed extension's backup into the backend. Idempotent.

Usage:
  .venv/Scripts/python.exe scripts/migrate_chrome_state.py backup/chrome-localstorage-2026-09-28.json

Accepts three file shapes: the localStorage export ({"value": state}), a chrome.storage dump
({"coachingState": state}), or the raw state ({"sites": ...}). Reads sites.gymdeskLive only:
its Gymdesk snapshot -> attendance import; its logs -> logs + log_received; replies -> replies +
reply_sent (sent_at unknown, so reply_seconds stays null). Never touches Chrome."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlmodel import Session, select  # noqa: E402

from app.db import init_db  # noqa: E402
from app.events import record  # noqa: E402
from app.models import Gym, Log, Reply  # noqa: E402
from app.slices.logs.service import create_log  # noqa: E402
from app.slices.roster.service import Snapshot, find_athlete, import_snapshot  # noqa: E402


def coaching_state(data: dict) -> dict:
    for key in ("value", "coachingState"):
        if isinstance(data.get(key), dict) and "sites" in data[key]:
            return data[key]
    if "sites" in data:
        return data
    raise SystemExit("No coaching state found in this file.")


def migrate(session: Session, gym: Gym, state: dict) -> dict:
    live = state.get("sites", {}).get("gymdeskLive") or {}
    snap = live.get("source")
    if not snap:
        raise SystemExit("gymdeskLive.source (the Gymdesk snapshot) is missing; nothing to key athletes on.")
    result = {"attendance": import_snapshot(session, gym, Snapshot.model_validate(snap)), "logs": 0, "replies": 0, "skipped": 0, "audio_dropped": 0}
    athlete = find_athlete(session, gym.id, gymdesk_member_id=snap["memberId"])
    for entry in live.get("logs", []):
        at = datetime.fromisoformat(entry["at"].replace("Z", "+00:00"))
        body = entry.get("body") or "(voice note without transcript)"
        if entry.get("audio"):
            result["audio_dropped"] += 1  # ponytail: base64 audio blobs are not migrated; Phase 4 stores media as files
        log = session.exec(select(Log).where(Log.athlete_id == athlete.id, Log.created_at == at, Log.transcript == body)).first()
        if log:
            result["skipped"] += 1
        else:
            log = create_log(session, gym, athlete, body, created_at=at, source="chrome_migration")
            result["logs"] += 1
        if entry.get("reply") and not session.exec(select(Reply).where(Reply.log_id == log.id)).first():
            session.add(Reply(log_id=log.id, body=entry["reply"], via="web", sent_at=None, reply_seconds=None))
            record(session, gym.id, "reply_sent", athlete_id=athlete.id, at=at,
                   meta={"log_id": log.id, "reply_seconds": None, "via": "web", "migrated": True, "sent_at_unknown": True})
            result["replies"] += 1
    session.commit()
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    state = coaching_state(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    with Session(init_db()) as session:
        gym = session.exec(select(Gym).order_by(Gym.id)).first()
        print(json.dumps(migrate(session, gym, state), indent=1))
