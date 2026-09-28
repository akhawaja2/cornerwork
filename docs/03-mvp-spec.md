# Cornerwork MVP — PRD, stack, structure, vertical slices

Status: draft v1 · Scope: live-wire demo + concierge pilot (Levels 2–3) · Out of scope: Mindbody sync, billing, athlete portal, video, RCS

---

## 1. PRD (short)

### Problem
Coaching stops when class ends. Coaches can't track what 100 people are working on; owners find out members are drifting only after attendance drops.

### Product
A texting-based coaching loop for gyms. Athletes text a gym number after class; AI summarizes and flags; the coach replies by voice or text; coaches get a pre-class brief; owners see early-warning signals.

### Users
| User | Job to be done | Surface |
|---|---|---|
| Athlete | Log a session in 30s, get coach feedback | SMS only (no app) |
| Coach | Reply to logs fast, walk into class informed | Web (phone-friendly) |
| Owner | See opt-ins, reply times, drift | Web |

### MVP feature list (must-have for pilot)
1. **Opt-in / opt-out** via `JOIN` / `STOP`, consent recorded with timestamp and message text.
2. **Log intake** — text or voice note → transcription → structured summary (techniques, sentiment, injury flag).
3. **Coach inbox** — logs with AI summary, one-tap reply, reply-time tracking.
4. **Coach reply** — from web or by texting the gym number from a registered coach phone; delivered to athlete as SMS.
5. **Pre-class brief** — per class: who's booked, flags (injury / returning / new / fight prep), themes from the week's logs, one suggested focus.
6. **After-class nudge** — scheduled prompt ~45 min after a booked class ends.
7. **Weekly recap** — Sunday SMS to each active athlete.
8. **Owner dashboard** — opt-ins, logging rate, median reply time, athletes with no log/attendance in 10+ days.
9. **Roster import** — CSV (name, phone, membership start). Bookings entered manually or via CSV.
10. **Event log** — every action recorded for pilot metrics.

### Non-goals (MVP)
Login for athletes, Mindbody/Gymdesk sync, payments, multi-gym tenancy UI (schema supports it), video, anonymous-feedback channel (pilot: a separate Google Form link), minors.

### Success metrics (pilot)
- ≥50% of opted-in athletes log ≥1×/week at week 4
- ≥80% of logs get a coach reply within 48h
- Coach time ≤2h/week per 20 athletes
- ≥10% of members offered the add-on opt in

### Safety rules (non-negotiable)
- AI never gives medical advice. Injury → flag to coach + "see a professional if it's serious" line. Concussion keywords → stronger referral text + immediate coach alert.
- Adults only. Consent text names the gym and Cornerwork. STOP always honored.
- No marketing messages. All outbound = service/transactional.

---

## 2. Tech stack decision

| Layer | Choice | Why | Alternative rejected |
|---|---|---|---|
| Language / API | **Python 3.12 + FastAPI** | You know it (APEX); async webhooks; Pydantic models double as LLM JSON schemas | Node/Next — fine, but two languages if LLM tooling is Python |
| DB | **SQLite via SQLModel** → Postgres at first paying gym | One file, zero ops, SQLModel migrates cleanly to Postgres | Postgres now — premature |
| Messaging | **Twilio Programmable Messaging** (SMS/MMS; RCS later) | Best docs, inbound media URLs, 10DLC handled in-console | WhatsApp — deferred (US adoption) |
| Transcription | **OpenAI Whisper API** (`whisper-1`) | Cents per minute, no GPU to run; swap to faster-whisper later if cost matters | faster-whisper self-hosted — more ops for a demo |
| LLM | **Claude (Sonnet)** via Anthropic SDK, tool-use for strict JSON | Reliable structured output; one prompt file per task | GPT — equivalent; pick one and stop |
| Frontend | **Jinja2 + HTMX + Pico.css** | One deployable, no build step, phone-friendly; HTMX polling for "live" inbox | React/Vite — you can, but it's a second app to deploy for a demo |
| Scheduler | **APScheduler** in-process | Nudges/recaps/briefs; fine for <50 gyms | Celery/Redis — overkill |
| Auth | **Magic-link email** for coach/owner (itsdangerous tokens); athletes have no login | Simplest secure option | Passwords — more code, worse UX |
| Deploy | **Fly.io** single machine + volume (or Railway) | HTTPS + persistent disk for SQLite/media in minutes | VPS — fine too |
| Media storage | Local volume for pilot → S3-compatible later | Voice notes are small; encrypt at rest when moving to S3 | |
| Tests | pytest + httpx; Twilio webhook payloads recorded as fixtures | Every slice ships with one end-to-end test | |
| Observability | structlog JSON + a `/health` route; Sentry free tier | Your day-job instinct; keep it light | |

**Principles:** one repo, one process, one DB file. Every external call (Twilio, Whisper, LLM) behind an interface with a fake for tests and for the offline demo mode.

---

## 3. Folder structure

```
cornerwork/
├── app/
│   ├── main.py                 # FastAPI app, routers, scheduler start
│   ├── config.py               # env settings (pydantic-settings)
│   ├── db.py                   # engine, session, init
│   ├── models.py               # SQLModel tables (see §4)
│   ├── events.py               # record(event_type, athlete_id, ...) → events table
│   ├── deps.py                 # auth deps: current_user, current_gym
│   ├── slices/                 # one folder per vertical slice
│   │   ├── optin/              # JOIN/STOP, consent
│   │   │   ├── router.py       # POST /sms (shared inbound router lives in inbound/)
│   │   │   ├── service.py
│   │   │   └── test_optin.py
│   │   ├── inbound/            # Twilio webhook: classify + dispatch to slice services
│   │   ├── logs/               # log intake, transcription, LLM parse, inbox
│   │   ├── replies/            # coach reply web + SMS
│   │   ├── brief/              # class brief generation + page
│   │   ├── nudges/             # after-class nudge, weekly recap (scheduler jobs)
│   │   ├── roster/             # CSV import, athletes, classes, bookings
│   │   └── owner/              # dashboard + metrics
│   ├── integrations/
│   │   ├── twilio_client.py    # send_sms(), fetch_media(); FakeTwilio for tests/demo
│   │   ├── transcribe.py       # whisper(); FakeTranscriber
│   │   └── llm.py              # parse_log(), build_brief(), write_recap(); FakeLLM
│   ├── prompts/
│   │   ├── parse_log.md
│   │   ├── class_brief.md
│   │   └── weekly_recap.md
│   ├── templates/              # Jinja: base.html, inbox.html, brief.html, owner.html, login.html
│   └── static/                 # pico.css, htmx.min.js, app.css
├── scripts/
│   ├── seed_demo.py            # 10 athletes, 2 weeks of logs, Thu 7pm class
│   └── import_roster.py
├── data/                       # cornerwork.db, media/ (gitignored)
├── tests/fixtures/twilio/      # recorded webhook payloads
├── .env.example
├── Dockerfile
├── fly.toml
└── README.md
```

Rule: a slice owns its router, service, templates fragment and test. Cross-slice calls go through `service.py` functions, never through another slice's router.

---

## 4. Data model

```
gyms            id, name, twilio_number, timezone, owner_email, created_at
users           id, gym_id, role(owner|head_coach|coach), name, email, phone(E.164, nullable), created_at
athletes        id, gym_id, name, phone(E.164, unique per gym), status(pending|active|stopped),
                coach_id(→users, nullable), photo_path, membership_start, goal, notes, created_at
consents        id, athlete_id, action(join|stop), raw_message, received_at, twilio_sid
messages        id, gym_id, athlete_id(nullable), direction(in|out), channel(sms|mms),
                from_phone, to_phone, body, media_path(nullable), twilio_sid, received_at, status
logs            id, athlete_id, message_id, transcript, summary, techniques(json[]),
                sentiment(pos|neutral|neg), injury(json|null: {area, severity, quote}),
                concussion_flag(bool), llm_model, created_at
flags           id, athlete_id, type(injury|returning|new|fight_prep|drift), source(ai|coach|system),
                detail, opened_at, resolved_at(nullable)
replies         id, log_id, coach_id, body, via(web|sms), message_id(out), sent_at,
                reply_seconds(int, computed at send)
classes         id, gym_id, name, coach_id, weekday, start_time, duration_min, discipline
bookings        id, class_id, athlete_id, class_date, status(booked|attended|no_show), source(csv|manual)
briefs          id, class_id, class_date, generated_at, content(json), sent_to_coach_at
drills          id, gym_id, coach_id, title, url, tags(json[])
events          id, gym_id, athlete_id(nullable), user_id(nullable), type, meta(json), at
```

**Event types** (the pilot's metrics come only from here): `opt_in, opt_out, log_received, log_parsed, injury_flagged, reply_sent, reply_read(rcs only), nudge_sent, recap_sent, brief_generated, brief_opened, booking_imported, check_in`.

**Derived views** (SQL, not tables): `weekly_logging_rate`, `median_reply_seconds`, `drift_candidates` (no log and no booking in 10 days).

---

## 5. Vertical slices

Each slice = one user-visible outcome, cut through webhook → service → DB → UI → test. Ship in order; each one is demoable on its own.

### Slice 0 — Skeleton (½ day)
- FastAPI app, SQLModel tables, `/health`, Fly deploy, `.env`, fakes for Twilio/Whisper/LLM, `DEMO_MODE=1` uses fakes.
- **Done when:** `curl https://app/health` returns 200 from Fly; `pytest` green with 1 test.

### Slice 1 — Opt-in / opt-out (½ day)
- Story: athlete texts `JOIN` → gets welcome + consent line; `STOP` → confirmed, status `stopped`, never messaged again.
- Inbound router: match `from_phone` to athlete (create `pending` if unknown), detect keywords, write `consents`, `events`.
- **Test:** fixture payload `JOIN` → athlete `active`, one outbound message, `opt_in` event. `STOP` → `stopped`, outbound blocked thereafter.
- **UI:** none.

### Slice 2 — Text log → inbox (1 day)
- Story: active athlete texts "Clinch felt sharper, kept getting countered off the jab, shin sore" → coach inbox shows summary, techniques, injury flag within 10s.
- `logs/service.py`: store message → `llm.parse_log()` (JSON: summary, techniques[], sentiment, injury|null, concussion_flag) → `logs`, `flags`, events.
- `templates/inbox.html`: list newest first, HTMX poll every 5s, badge for injury.
- Magic-link login for coach.
- **Test:** fixture text → log row with `injury.area == "shin"`; inbox HTML contains athlete name.
- **Prompt rule:** if `concussion_flag`, append referral line to the athlete's auto-ack.

### Slice 3 — Voice note log (½ day)
- Story: same as slice 2, but the athlete sends an audio message.
- Fetch Twilio media → `data/media/` → `transcribe()` → same pipeline. Auto-ack "Got it — Coach Sam will reply."
- **Test:** MMS fixture with fake audio → transcript stored → log parsed.

### Slice 4 — Coach reply (½ day)
- Story: coach types a reply in the inbox → athlete receives SMS "Coach Sam: …" → reply time recorded.
- `replies/router.py` POST; `twilio_client.send_sms`; `reply_seconds = sent_at − log.created_at`.
- Optional drill picker (select from `drills`) appends a link.
- **Test:** POST reply → outbound message row, `reply_sent` event, `reply_seconds > 0`.

### Slice 5 — Seed + class brief (1 day)
- Story: open `/brief/{class_id}/{date}` → booked athletes with flags, week's themes, suggested focus, new-member row.
- `scripts/seed_demo.py`: 10 athletes, 2 weeks of realistic logs, a Thu 7pm class, bookings.
- `brief/service.py`: gather bookings + last-7-day logs + open flags → `llm.build_brief()` → `briefs`.
- **Test:** seeded DB → brief JSON has ≥1 flag and a `focus` string; page renders.
- **Demo checkpoint:** this + slices 1–4 is the live-wire meeting demo.

### Slice 6 — After-class nudge (½ day)
- Story: 45 min after a booked class ends, each `attended`/`booked` athlete gets "Good session? Voice note or text: what clicked, anything sore?"
- APScheduler job every 5 min: find classes ended in window, send once per athlete/day (idempotent via events).
- Frequency cap: max 1 outbound nudge per athlete per day; quiet hours 22:00–08:00 gym-local.
- **Test:** freeze time → job sends exactly one nudge; re-run sends none.

### Slice 7 — Coach reply by SMS (½ day)
- Story: coach texts/voice-notes the gym number from their registered phone → routed as a reply to that coach's most recent unanswered log (or `#athletename` prefix to target).
- Inbound router: if `from_phone` matches a `users.phone`, treat as reply, transcribe if audio.
- **Test:** coach-phone fixture → reply attached to correct log, athlete receives it.

### Slice 8 — Weekly recap (½ day)
- Story: Sunday 18:00 gym-local, each active athlete gets a 3-line recap (sessions, focus, coach note, next step).
- Scheduler job → `llm.write_recap()` → SMS. Skip athletes with zero logs (send a gentle "no logs this week?" at most every 2 weeks).
- **Test:** seeded athlete → recap text ≤ 320 chars, `recap_sent` event.

### Slice 9 — Owner dashboard (1 day)
- Story: owner opens `/owner` → opt-ins, % logging this week, median reply time, drift list, per-coach reply stats.
- All numbers from `events` + derived SQL views. HTMX table, no charts yet.
- **Test:** seeded events → dashboard values match hand-computed fixtures.

### Slice 10 — Roster + bookings CSV import (½ day)
- Story: owner uploads `athletes.csv` and `bookings.csv` (Mindbody/Gymdesk export shape) → rows created/updated by phone.
- `scripts/import_roster.py` + `/owner/import` form.
- **Test:** sample CSV → 20 athletes, 40 bookings, idempotent re-import.

### Slice 11 — Pilot hardening (½ day)
- 10DLC registration done; Sentry; nightly SQLite backup to S3; `DEMO_MODE` offline path verified; consent copy reviewed by counsel.

**Total:** ~7–8 focused days. Demo-ready after slice 5 (~3½ days).

### Backlog (post-pilot, only if gates pass)
Mindbody webhooks → `roster` slice · Gymdesk via Zapier webhook · Stripe Connect payouts · athlete magic-link progress page · per-discipline coach routing · RCS sender · WhatsApp channel · anonymous feedback + confidential concern routing · VLM clip hints.

---

## 6. LLM contract for `parse_log` (the one prompt that matters)

Input: transcript + athlete goal + last 3 summaries.
Output JSON (validated with Pydantic, retried once on failure):

```json
{
  "summary": "≤ 2 sentences, athlete's own words where possible",
  "techniques": ["jab exit angle", "clinch entry"],
  "sentiment": "pos|neutral|neg",
  "injury": {"area": "left shin", "severity": "minor|moderate|serious|unknown", "quote": "shin sore after checks"} ,
  "concussion_flag": false,
  "coach_draft": "1–2 sentence suggested reply for the coach to edit"
}
```

Rules in the prompt: never diagnose; never suggest training through pain; concussion/head/dizzy/blackout → `concussion_flag: true`; unknown → `null`, not guesses.
