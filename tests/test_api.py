import pytest
from sqlmodel import Session, select

from app import db
from app.events import record
from app.models import Event
from tests.conftest import SNAPSHOT


def test_init_db_creates_tables_and_events_record(client):
    with Session(db.engine) as s:
        record(s, 1, "opt_in", athlete_id=None, meta={"fixture": True})
        s.commit()
        assert s.exec(select(Event)).one().type == "opt_in"
        with pytest.raises(ValueError):
            record(s, 1, "not_a_real_type")
    assert client.get("/health").json() == {"ok": True}


def test_bearer_token_required(client):
    assert client.get("/health").status_code == 200
    for headers in ({}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic abc"}):
        r = client.get("/api/inbox", headers={**headers, "Authorization": headers.get("Authorization", "")})
        assert r.status_code == 401, r.text
    assert client.get("/c/test-token").status_code == 200
    assert client.get("/c/wrong").status_code == 404


def test_inbox_shows_log_then_reply(client, sarah_log):
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["transcript"] == "Class was OK, Abu is excellent" and log["reply"] is None
    r = client.post("/api/replies", json={"log_id": sarah_log["log_id"], "body": "Thanks!"})
    assert r.status_code == 201, r.text
    assert r.json()["reply_seconds"] >= 0
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["reply"]["body"] == "Thanks!" and log["athlete"]["name"] == "Sarah Demo"


def test_inbox_scoped_to_gymdesk_member(client, sarah_log):
    scoped = client.get("/api/inbox?member=12672454").json()
    assert scoped["athlete"]["name"] == "Sarah Demo" and len(scoped["logs"]) == 1
    unknown = client.get("/api/inbox?member=999").json()
    assert unknown["athlete"] is None and unknown["logs"] == []
    by_id = client.get(f"/api/inbox?athlete={sarah_log['athlete_id']}").json()
    assert by_id["athlete"]["name"] == "Sarah Demo" and len(by_id["logs"]) == 1
    assert client.get("/api/inbox?athlete=999").json()["athlete"] is None
    assert "athlete" not in client.get("/api/inbox").json()


def test_reply_rejects_duplicate_and_unknown_log(client, sarah_log):
    assert client.post("/api/replies", json={"log_id": sarah_log["log_id"], "body": " "}).status_code == 422
    assert client.post("/api/replies", json={"log_id": 999, "body": "x"}).status_code == 404
    assert client.post("/api/replies", json={"log_id": sarah_log["log_id"], "body": "Thanks!"}).status_code == 201
    assert client.post("/api/replies", json={"log_id": sarah_log["log_id"], "body": "Again"}).status_code == 409


def test_import_attendance_is_idempotent_and_feeds_brief(client):
    first = client.post("/api/import/attendance", json=SNAPSHOT)
    assert first.status_code == 200, first.text
    assert first.json()["created"] == 1
    second = client.post("/api/import/attendance", json=SNAPSHOT).json()
    assert second["created"] == 0 and second["athlete_id"] == first.json()["athlete_id"]
    with Session(db.engine) as s:
        checkins = s.exec(select(Event).where(Event.type == "check_in")).all()
        assert len(checkins) == 1 and checkins[0].meta["gymdesk_row_id"] == "62252846"
        assert checkins[0].at.isoformat() == "2026-09-28T11:00:00+00:00"  # 07:00 America/New_York -> UTC
    brief = client.get("/api/brief/1/2026-09-28").json()
    assert brief["class"]["name"] == "Cornerwork Test — Boxing" and brief["class"]["start_time"] == "07:00"
    assert [a["name"] for a in brief["athletes"]] == ["Sarah Demo"] and brief["sources"] == ["gymdesk"]
    assert client.get("/api/brief/1/2026-09-29").json()["athletes"] == []  # Box 09-29 has no imported booking
    assert client.get("/api/brief/99/2026-09-28").status_code == 404
    assert client.post("/api/import/attendance", json={**SNAPSHOT, "gym": "Other Gym"}).status_code == 400
    bad = {**SNAPSHOT, "records": [{**SNAPSHOT["records"][0], "date": "02/31/2026"}]}
    assert client.post("/api/import/attendance", json=bad).status_code == 422


def test_import_roster_upserts_and_records_bookings(client):
    roster = {"athletes": [{"name": "Alex Demo", "phone": "+15550000002", "gymdesk_member_id": "12672458"}],
              "bookings": [{"class_name": "Box", "class_date": "2026-09-29", "status": "booked", "phone": "+15550000002",
                            "start_time": "07:00", "duration_min": 60}]}
    assert client.post("/api/import/roster", json=roster).json()["bookings_created"] == 1
    assert client.post("/api/import/roster", json=roster).json()["bookings_created"] == 0
    missing = {"bookings": [{"class_name": "Box", "class_date": "2026-09-29", "status": "booked", "phone": "+15550009999"}]}
    assert client.post("/api/import/roster", json=missing).status_code == 422
    assert client.post("/api/import/roster", json={"athletes": [{"name": "No key"}]}).status_code == 422
    brief = client.get("/api/brief/1/2026-09-29").json()
    assert brief["athletes"][0]["name"] == "Alex Demo" and brief["sources"] == ["csv"]


def test_owner_summary_from_events(client, sarah_log):
    before = client.get("/api/owner/summary").json()
    assert before["coached"] == 1 and before["total_logs"] == 1 and before["unanswered_logs"] == 1 and before["reply_rate"] == 0.0
    client.post("/api/replies", json={"log_id": sarah_log["log_id"], "body": "Thanks!"})
    after = client.get("/api/owner/summary").json()
    assert after["total_replies"] == 1 and after["reply_rate"] == 100.0 and after["replied_within_48h_rate"] == 100.0
    assert after["weekly_logging_rate"] == 100.0 and after["drift"] == [] and after["computed_from"] == "events"
