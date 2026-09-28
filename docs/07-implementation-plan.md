# 07 — Implementation plan: extension-as-app + phone PWA

Scope: take the current pilot (Gymdesk import in the installed extension, Sarah's data, FastAPI demo) to a working coach/owner product on desktop (extension) and phone (magic-link PWA), with athletes on SMS. Target: demo-ready in ~2 weeks of evenings, pilot-ready in ~4.

Repo: `C:/Users/Abu/Documents/Python/CornerWork`. Companion docs: `03-mvp-spec.md` (data model, LLM contract), `06-extension-handoff-revised.md` (what exists, decisions).

---

## Phase 0 — Protect the work (Day 1, ~1 hr)

| # | Task | Done when |
|---|---|---|
| 0.1 | `git init`, `.gitignore` (`demo/data/`, `node_modules/`, `.env`, `*.sqlite3`), first commit, push to a private GitHub repo | Remote exists; `git log` shows the commit |
| 0.2 | Export the installed extension's `chrome.storage.local` (`coachingState`, `gymdeskSnapshot`) to `backup/chrome-storage-2026-09-28.json` via the extension's service-worker console | File contains the "Thanks!" reply |
| 0.3 | `.env.example` with `TWILIO_*`, `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`, `BACKEND_URL`, `PUBLIC_URL` | Documented, nothing committed |

Risk covered: the prior session left no commit; one machine failure loses everything.

---

## Phase 1 — Backend becomes the store (Days 2–4)

Keep `demo/core.py` domain logic; strip `demo/static/index.html` to reference material.

| # | Task | Files | Done when |
|---|---|---|---|
| 1.1 | Migrate schema to spec tables: `gyms, users, athletes, consents, messages, logs, flags, replies, classes, bookings, briefs, drills, events` (SQLModel) | `app/models.py`, `app/db.py` | `pytest` creates the DB; `events.record()` works |
| 1.2 | JSON API for the extension: `GET /api/inbox`, `GET /api/brief/{class_id}/{date}`, `POST /api/replies`, `POST /api/import/attendance`, `POST /api/import/roster`, `GET /api/owner/summary` | `app/slices/*/router.py` | Each route has one httpx test with fixtures |
| 1.3 | Token auth: `Authorization: Bearer <gym_token>`; token issued by `scripts/issue_token.py`; stored by the extension | `app/deps.py` | Requests without token → 401 |
| 1.4 | Import upsert: athletes keyed by `(gym_id, gymdesk_member_id)`; bookings by `(class_id, athlete_id, class_date)`; idempotent | `app/slices/roster/service.py` | Re-posting Sarah's snapshot creates 0 new rows |
| 1.5 | One-time migration script: reads `backup/chrome-storage-*.json` → `logs`, `replies`, `events` | `scripts/migrate_chrome_state.py` | "Thanks!" reply visible via `GET /api/inbox` |
| 1.6 | Serve the dashboard bundle at `GET /c/{token}` (static files + injected `window.CW_ADAPTER="web"`) | `app/main.py` | Route returns 200 with the bundle (bundle arrives in Phase 2) |

Exit test: `curl -H "Authorization: Bearer …" localhost:8765/api/inbox` returns Sarah's log and the reply.

---

## Phase 2 — The dashboard bundle (Days 5–9)

One codebase, three containers. **Rule: components never call `chrome.*`.**

| # | Task | Files | Done when |
|---|---|---|---|
| 2.1 | `adapter.js` interface: `getState()`, `subscribe(cb)`, `post(path, body)`, `openLink(url)`, `cache.get/set` | `extension-demo/adapter.js` | Two impls: `adapter.extension.js` (chrome.storage + runtime messaging → background fetch), `adapter.web.js` (fetch + localStorage) |
| 2.2 | `dashboard.html` shell + router (hash routes: `#inbox`, `#brief`, `#owner`) | `extension-demo/dashboard.html`, `dashboard.js` | Loads in an extension tab and as a plain file |
| 2.3 | **Inbox** component: list logs newest-first; summary/tags/injury badge (placeholders until Phase 3); reply box; drill picker; "sent" state | `components/inbox.js` | Reply → `POST /api/replies` → appears in list with reply time |
| 2.4 | **Brief** component: class header, booked athletes with flags/photos, themes, suggested focus; "demo data" label when bookings are synthetic | `components/brief.js` | Box 09-29 brief renders from real imported attendance |
| 2.5 | **Owner** component: coached count, logging % this week, median reply time, early-warning list | `components/owner.js` | Values match `/api/owner/summary` |
| 2.6 | Toolbar click → `chrome.tabs.create({url: chrome.runtime.getURL("dashboard.html")})`; on Gymdesk pages also `sidePanel.open` | `background.js` | Both open the same bundle |
| 2.7 | Side panel: `panel.html` becomes a thin wrapper around `dashboard.html#brief` with the class detected from the Gymdesk URL | `panel.html`, `gymdesk-reader.js` | Opening a Gymdesk class page shows that class's brief |
| 2.8 | Offline: cached last state renders with a "stale · last synced 12m ago" bar when the backend is unreachable | `adapter.*.js` | Kill the backend; dashboard still shows data, marked stale |
| 2.9 | Retire `lab.js`/`voice.js` from the product path (`?harness=1` guard); delete old `panel.js` UI | — | No product link reaches the harness |

Exit test: coach opens the extension tab, sees Sarah's log + reply, opens the Box brief, sends a reply from the tab, sees it in `/api/inbox`.

---

## Phase 3 — AI in the loop (Days 10–11)

| # | Task | Files | Done when |
|---|---|---|---|
| 3.1 | `parse_log` prompt + Pydantic schema per spec §6 (summary, techniques, sentiment, injury, concussion_flag, coach_draft); retry once on invalid JSON | `app/prompts/parse_log.md`, `app/integrations/llm.py` | "Class was OK, Abu is excellent" → sentiment `pos`; "shin sore after checks" → injury `{area: "left shin"}` |
| 3.2 | Run on every new log; store `llm_model`; inbox shows summary + editable `coach_draft` | `app/slices/logs/service.py`, `components/inbox.js` | Draft appears; coach edits; edit distance recorded in `events` (`reply_sent.meta.edit_distance`) |
| 3.3 | Brief generator: bookings + last-7-day logs + open flags → `build_brief()` | `app/prompts/class_brief.md`, `app/slices/brief/service.py` | Brief JSON has ≥1 flag and a `focus` string on seeded data |
| 3.4 | Safety rules in prompt + post-check: no medical advice; concussion keywords → referral line + coach alert | `llm.py`, tests | Fixture "hit my head, dizzy" → `concussion_flag: true`, referral text in auto-ack |
| 3.5 | Eval set: 50 real/realistic logs with coach-approved answers; `scripts/eval.py` reports acceptance proxy | `tests/eval/` | Runs in <2 min; baseline number recorded |

---

## Phase 4 — Athletes on SMS (Days 12–14)

| # | Task | Files | Done when |
|---|---|---|---|
| 4.1 | Twilio number + business-texting (10DLC) registration **started on Day 1** (takes days) | — | Registration submitted |
| 4.2 | Tunnel for local dev (`cloudflared` or ngrok) → `PUBLIC_URL`; Twilio webhook → `POST /sms` | `app/slices/inbound/router.py` | Twilio console shows 200s |
| 4.3 | `JOIN`/`STOP` handling, consent rows, welcome + STOP confirmation; phone → athlete match (create `pending` if unknown) | `app/slices/optin/` | Test phone texts JOIN → `active`; STOP → `stopped`, outbound blocked |
| 4.4 | Text log intake → `parse_log` → inbox | `app/slices/logs/` | Text from test phone appears in the extension inbox within 10 s |
| 4.5 | Outbound reply from inbox → SMS signed "Coach Sam:" | `app/integrations/twilio_client.py` | Reply lands on the test phone; `reply_seconds` recorded |
| 4.6 | MMS audio → download → Whisper → same pipeline; auto-ack "Got it, Coach Sam will reply" | `app/integrations/transcribe.py` | Voice note from test phone → transcript → log |

Exit test (the demo script from `04-demo-and-pilot.md`): owner texts the number, coach sees it in the extension, replies, owner gets the reply, brief updates.

---

## Phase 5 — Phone (Days 15–16)

| # | Task | Files | Done when |
|---|---|---|---|
| 5.1 | Backend serves bundle at `/c/{token}` with `adapter.web.js`; token = per-user magic link (30-day expiry, rotate endpoint) | `app/main.py`, `app/deps.py` | Link opens dashboard on a phone with no login |
| 5.2 | PWA: `manifest.webmanifest`, `sw.js` (cache shell + last state), icons | `extension-demo/web/` | "Add to Home Screen" works on iOS and Android; opens standalone |
| 5.3 | Brief-by-SMS: 90 min before class, coach gets "Box · 7pm · 14 booked · 1 flag → link" | scheduler job | Message arrives; link opens the brief |
| 5.4 | Responsive pass on inbox/brief (390 px), 44 px targets | components | Usable one-handed |

---

## Phase 6 — Scheduler + roster (Days 17–19)

| # | Task | Done when |
|---|---|---|
| 6.1 | APScheduler: after-class nudge 45 min post-class for booked/attended athletes; 1/day cap; quiet hours 22:00–08:00 | Freeze time test sends exactly one nudge |
| 6.2 | Sunday recap SMS per active athlete | Recap ≤320 chars; `recap_sent` event |
| 6.3 | Gymdesk **schedule/roster** import in `gymdesk-reader.js` (class list + booked members from DOM) → `POST /api/import/roster` | Real bookings drive the brief; "demo data" label gone |
| 6.4 | Owner early-warning: no log/attendance 10+ days → list + "ask coach to check in" (creates a coach task) | Appears for a seeded stale athlete |

---

## Phase 7 — Pilot hardening (Days 20–22)

| # | Task | Done when |
|---|---|---|
| 7.1 | Deploy backend to Fly.io with volume; nightly SQLite backup to S3-compatible storage | `/health` green from Fly; backup file exists |
| 7.2 | Sentry + structlog; `DEMO_MODE=1` offline path verified | Demo runs with network off |
| 7.3 | Consent copy reviewed (TCPA wording names gym + Cornerwork, STOP, 18+) | Reviewed by counsel or checklist signed |
| 7.4 | Private extension distribution to pilot coaches (unpacked or unlisted Web Store) | 2 coaches installed on their machines |
| 7.5 | Metrics dashboard for you: events → weekly logging %, reply time, coach minutes, opt-in % | Matches `02-validation-plan.md` gates |

---

## Sequence and dependencies

```
Day 1   P0 backup+git ─┬─ P4.1 start 10DLC (async, days)
Days 2–4   P1 backend ──┐
Days 5–9   P2 bundle ───┼── needs P1.2 API
Days 10–11 P3 AI ───────┼── needs P1, P2.3
Days 12–14 P4 SMS ──────┼── needs P3, tunnel, 10DLC for non-test phones
Days 15–16 P5 phone ────┼── needs P2 adapter + P1.6
Days 17–19 P6 sched ────┼── needs P4, P6.3 needs gymdesk-reader
Days 20–22 P7 pilot
```

**Demo-ready** after Phase 4 (owner texts, coach replies from extension). **Pilot-ready** after Phase 7.

---

## Risks and what to do about them

| Risk | Mitigation |
|---|---|
| Gymdesk markup changes break `gymdesk-reader.js` | Selectors in one file; fixture HTML in tests; CSV import as fallback |
| `chrome.*` leaks into components → phone build breaks | ESLint rule banning `chrome` global outside `adapter.extension.js`/`background.js` |
| 10DLC delays SMS to real athletes | Start Day 1; test phones work before approval |
| Coaches don't reply | Instrument from day 1; it's the pilot's kill criterion, not an engineering problem |
| Losing the installed-Chrome data | Phase 0.2 backup before any storage change |
| LLM cost/latency | Batch briefs; cache parse results; small model for parse, larger for brief |

---

## Definition of done (pilot)

- Athlete texts → log in extension inbox in <10 s, with summary and draft.
- Coach replies from extension or phone; athlete receives it; `reply_seconds` recorded.
- Brief for a real Gymdesk class shows booked athletes, flags, focus, 90 min before class, on desktop and phone.
- Owner sees coached count, logging %, reply times, early-warning list.
- Every action is an `events` row; the validation-plan metrics compute from it.
- Backend on Fly.io, backed up nightly; extension installed by 2 pilot coaches; git remote current.
