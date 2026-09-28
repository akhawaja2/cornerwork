from sqlmodel import Session, select

from app import db
from app.integrations.twilio_client import signature
from app.models import Athlete, Event, Message
from app.slices.inbound.router import coach_name

PHONE = "+15550000001"


def sms(client, body="", **extra):
    return client.post("/sms", data={"From": PHONE, "To": "+15550000000", "MessageSid": "SM" + str(abs(hash(body)) % 10**6),
                                     "Body": body, "NumMedia": "0", **extra})


def text_of(response):
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/xml")
    return response.text


def test_join_consent_log_reply_stop(client):
    # Unknown number: created pending, told to JOIN, no log.
    assert "JOIN" in text_of(sms(client, "hello"))
    assert client.get("/api/inbox").json()["logs"] == []
    assert "YES 18" in text_of(sms(client, "JOIN"))
    assert "18 or older" in text_of(sms(client, "YES"))
    assert "You are in" in text_of(sms(client, "yes 18"))
    with Session(db.engine) as s:
        athlete = s.exec(select(Athlete).where(Athlete.phone == PHONE)).one()
        assert athlete.status == "active"
        assert [e.type for e in s.exec(select(Event)).all()] == ["opt_in"]
    # Text log -> parsed log, injury ack, inbox.
    ack = text_of(sms(client, "Clinch felt sharper. Left shin sore after checks."))
    assert "medical" in ack and "shin" in ack
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["injury"]["area"] == "shin" and log["athlete"]["status"] == "active" and log["coach_draft"]
    # Coach reply from the dashboard -> outbound SMS row (simulated, no credentials).
    r = client.post("/api/replies", json={"log_id": log["id"], "body": "Rest the shin; see you Thursday."})
    assert r.status_code == 201 and r.json()["message_id"]
    with Session(db.engine) as s:
        out = s.get(Message, r.json()["message_id"])
        assert out.direction == "out" and out.status == "simulated" and out.body.startswith(coach_name() + ":") and out.to_phone == PHONE
    # Concussion ack.
    assert "head knock" in text_of(sms(client, "took a knee to the head, dizzy after"))
    # STOP: no more texts at all.
    assert "opted out" in text_of(sms(client, "STOP"))
    assert "<Message>" not in text_of(sms(client, "still here?"))
    with Session(db.engine) as s:
        assert s.exec(select(Athlete).where(Athlete.phone == PHONE)).one().status == "stopped"
        assert "opt_out" in [e.type for e in s.exec(select(Event)).all()]
    # Reply to a stopped athlete stores the reply but sends nothing.
    log2 = client.get("/api/inbox").json()["logs"][0]
    r = client.post("/api/replies", json={"log_id": log2["id"], "body": "Please get checked."})
    assert r.status_code == 201 and r.json()["message_id"] is None


def test_voice_note_uses_transcriber(client):
    sms(client, "JOIN")
    sms(client, "YES 18")
    ack = text_of(sms(client, "", NumMedia="1", MediaUrl0="https://api.twilio.com/media/x", MediaContentType0="audio/ogg"))
    assert "medical" in ack  # demo transcript mentions a sore shin
    log = client.get("/api/inbox").json()["logs"][0]
    assert log["transcript"].startswith("[demo transcript]") and log["injury"]["area"] == "shin"
    with Session(db.engine) as s:
        assert s.exec(select(Event).where(Event.type == "log_received")).one().meta["source"] == "mms:fake-transcript"


def test_signature_vector_and_rejection(client, monkeypatch):
    # Vector from Twilio's security docs.
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    params = {"CallSid": "CA1234567890ABCDE", "Caller": "+12349013030", "Digits": "1234", "From": "+12349013030", "To": "+18005551212"}
    assert signature(url, params, "12345") == "0/KCTR6DLpKmkAf8muzZqo1nDgQ="
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "12345")
    monkeypatch.setenv("PUBLIC_URL", "https://example.test")
    body = {"From": PHONE, "To": "+15550000000", "Body": "JOIN", "NumMedia": "0", "MessageSid": "SM1"}
    assert client.post("/sms", data=body).status_code == 403
    assert client.post("/sms", data=body, headers={"X-Twilio-Signature": "nope"}).status_code == 403
    good = signature("https://example.test/sms", body, "12345")
    assert client.post("/sms", data=body, headers={"X-Twilio-Signature": good}).status_code == 200
