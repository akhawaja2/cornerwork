from sqlmodel import Session, select

from app import db
from app.deps import gym_for_token
from app.integrations.llm import FakeLLM, edit_distance, safety_check
from app.models import Athlete, Event, Flag
from app.slices.logs.service import create_log
from scripts.eval import run


def intake(text):
    with Session(db.engine) as s:
        gym = gym_for_token(s, "test-token")
        athlete = s.exec(select(Athlete)).first() or Athlete(gym_id=gym.id, name="Sarah Demo", status="active", goal="cleaner technique")
        s.add(athlete)
        s.flush()
        log = create_log(s, gym, athlete, text)
        s.commit()
        return log.id


def test_fake_parse_positive_and_injury(client):
    log_id = intake("Class was OK, Abu is excellent")
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["id"] == log_id and log["sentiment"] == "pos" and log["injury"] is None and not log["concussion_flag"]
    assert log["coach_draft"] and log["llm_model"] == "fake-rules"
    intake("Clinch felt sharper. My left shin is sore after checks.")
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["injury"]["area"] == "shin" and log["injury"]["severity"] == "unknown" and "clinch" in log["techniques"]
    assert "medical" in log["coach_draft"].lower()
    with Session(db.engine) as s:
        flags = s.exec(select(Flag)).all()
        assert len(flags) == 1 and flags[0].type == "injury" and flags[0].source == "ai"
        types = [e.type for e in s.exec(select(Event)).all()]
        assert types.count("log_parsed") == 2 and types.count("injury_flagged") == 1


def test_concussion_flag_and_coach_alert(client):
    intake("hit my head in sparring, bit dizzy after")
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["concussion_flag"] is True and log["injury"]["area"] == "head"
    assert "medical" in log["coach_draft"].lower()
    with Session(db.engine) as s:
        event = s.exec(select(Event).where(Event.type == "injury_flagged")).one()
        assert event.meta["concussion"] is True


def test_safety_check_overrides_a_permissive_parse():
    parsed = FakeLLM().parse_log("felt great", "", [])
    parsed.concussion_flag = False
    fixed = safety_check("blacked out for a second after a knee to the head, feel fine", parsed)
    assert fixed.concussion_flag is True and fixed.injury and fixed.injury.area == "head"
    assert "medical" in fixed.coach_draft.lower()


def test_reply_records_edit_distance(client):
    log_id = intake("Jab felt sharper today")
    draft = client.get("/api/inbox").json()["logs"][0]["coach_draft"]
    r = client.post("/api/replies", json={"log_id": log_id, "body": draft + " See you Thursday."})
    assert r.status_code == 201
    with Session(db.engine) as s:
        meta = s.exec(select(Event).where(Event.type == "reply_sent")).one().meta
        assert meta["edit_distance"] == len(" See you Thursday.") and meta["draft_len"] == len(draft)
    assert edit_distance("kitten", "sitting") == 3 and edit_distance("", "abc") == 3


def test_eval_floor_on_fake():
    result = run(FakeLLM())
    assert result["concussion"] == 100, result
    assert result["injury"] >= 90, result
    assert result["sentiment"] >= 80, result
