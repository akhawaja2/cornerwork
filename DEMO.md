# Cornerwork local MVP demo

A working, offline demonstration of the coaching loop in `docs/03-mvp-spec.md` and `docs/04-demo-and-pilot.md`. This is a local demo, not a live SMS pilot. It uses fictional adult athletes and sends no real messages.

## Start

From the project folder, run:

```powershell
.\start-demo.ps1
```

Open http://127.0.0.1:8765. The launcher creates `.venv` and installs `demo/requirements.txt` if needed. Initial installation needs internet; running the installed demo does not. Python 3.12 or newer is required. Stop with Ctrl+C.

Alternatively:

```powershell
.\.venv\Scripts\python.exe demo\server.py
```

Data persists in `demo/data/demo.sqlite3`. The demo reset button restores fictional fixtures. The server binds only to `127.0.0.1`; do not expose it on a network or put real customer information into it. Coach/owner views are a demo navigation choice, not authentication.

## Architecture

- `demo/core.py`: SQLite domain logic, fixtures, simulated intake, replies, brief, scheduled messages, imports and metrics.
- `demo/server.py`: FastAPI JSON endpoints and the local page.
- `demo/static/index.html`: responsive interface; no npm, CDN or frontend build.
- `demo/test_core.py`: domain acceptance tests.
- `demo/test_server.py`: HTTP integration tests.

This deliberately simplifies the draft's slice folders, SQLModel, HTMX and separate SDK interfaces. There is one small domain module and one HTTP wrapper, using standard-library SQLite. External behavior is represented by deterministic local functions and a persisted simulated message ledger. The functional scope remains traceable to the written MVP.

## Demo walkthrough

1. Open the class brief. Inspect booked athletes, flags, recent training themes and the suggested focus.
2. In Demo tools, select a fictional athlete and submit a training message, such as: `Clinch felt sharper, kept getting countered off the jab, shin sore`.
3. Open the coach inbox. Inspect the original message, simulated structured summary, tags and injury flag.
4. Write a coach reply and send it. Inspect the simulated conversation to see the outgoing message and recorded reply time.
5. Return to the brief: the booked athlete's latest context contributes to it. A log does not automatically enroll an unbooked athlete in a class.
6. Try the simulated voice input. Its text is a supplied transcript fixture; there is no microphone recording or speech recognition.
7. Explore the owner metrics and CSV imports. In Demo tools, run scheduled jobs at a selected time to demonstrate nudges and recaps.
8. Test consent on a pending/new number: `JOIN`, then `YES 18`. `STOP` records withdrawal and blocks further service messages.

## Scope and deliberate boundaries

| Documented behavior | Local demonstration | Production boundary |
|---|---|---|
| JOIN/STOP and adults-only consent | Persisted commands and explicit adult acknowledgement | Actual SMS consent copy/provider setup need review |
| Text intake | Persisted message to structured coach log | Parsing uses deterministic rules, not an LLM |
| Voice intake | Explicit transcript fixture enters the same pipeline | No audio fetch/storage/Whisper integration |
| Coach web/SMS reply | Real local state changes and simulated message delivery | No Twilio webhook, credentials or delivery receipts |
| Brief | Computed from selected bookings and stored context | No booking-provider sync |
| Nudges and recaps | Clock-controlled, idempotent local job runner | No always-on production scheduler |
| Owner dashboard | Calculated from stored activity | Seeded history is fictional, not pilot results |
| Roster/bookings | Validated CSV import | CSV format is documented in the UI; not an arbitrary vendor export parser |
| Events | Persisted action log | No production monitoring or external analytics |
| Access | Local coach/owner presentation | No magic-link authentication or email delivery |
| Pilot hardening | Local acceptance tests | No deployment, 10DLC, Sentry, S3 backups or legal sign-off |

AI-like text is labeled simulated. Summaries can miss language that falls outside the demo rules; they must not be treated as reliable injury or confidential-concern detection. A human coach sends replies. Injury text receives a generic referral rather than a diagnosis. Confidential examples are separated into the owner view; this is not secure multi-user access control.

## Product choices kept open

- No billing or prices appear in the app. The docs' original revenue split and later flat gym fee are competing proposals.
- Reply timestamps are measured; the app does not choose between a weekly service and a 48-hour commitment.
- The written spec takes precedence over design concepts for scope: no athlete portal, video, RCS, WhatsApp, multi-gym administration or integrations.
- Coach SMS targeting is explicit rather than silently choosing the most recent athlete. This prevents a demo from normalizing ambiguous delivery.
- Drift is a transparent demo signal, not a churn prediction. The dashboard states its implemented definition.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s demo -p 'test_*.py' -v
```

The tests use temporary databases and do not change the running demo's data. See the completion notes for the final verification results and any remaining limitations.

## Completion evidence — 28 September 2026

- `python -m unittest discover -s demo -p 'test_*.py' -v`: **28 passing tests** (22 domain, 6 HTTP).
- `demo/browser-check.cjs`: browser submission → inbox → coach reply → conversation verified; scheduled nudge preset sends; owner view and all five views at 390px pass; no browser page errors.
- Visual inspection: desktop brief, owner overview and mobile brief screenshots in `demo/screenshots/`.
- Running server `/health`: `ok: true`, `mode: offline-demo`, `external_services: false`.
- Clean reset: ten fictional athletes, eight active opt-ins, six recent loggers (75%), 25 logs and 19 replies before interaction.

Browser checks use Playwright (available in the bundled Codex Node runtime). `browser-check.cjs` and `capture-demo.cjs` intentionally reset the local fictional database; do not use them on data you want to preserve. They are optional verification tools, not dependencies for using the app. `capture-demo.cjs` restores the clean seed and saves screenshots.

The application is served by a background local process for this handoff. If it is no longer running, use `start-demo.ps1` again. The port can be changed with the `PORT` environment variable; the optional browser scripts target port 8765.

The HTTP test client currently emits a dependency deprecation warning about httpx; all checks complete successfully. This does not affect the demo server or browser flow.
