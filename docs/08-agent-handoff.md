# Cornerwork — agent handoff (for Claude Code / Cowork)

Read this first. Then `07-implementation-plan.md` for the task list, `06-extension-handoff-revised.md` for what exists, `03-mvp-spec.md` for the data model and LLM contract. Do not re-derive product decisions; they are settled below.

## 1. What you are building

Cornerwork: coaching between classes for gyms. Athletes **text** a gym number after training (SMS/RCS via Twilio). A backend transcribes, summarizes, tags techniques and flags injuries. Coaches reply and view a pre-class brief from a **Chrome extension** (desktop) or the **same dashboard served at a magic link** (phone, PWA). Owners see early-warning, coached-tier numbers and reply times in the same dashboard.

**The extension is the app for staff. Athletes never install anything. The backend has no pages except the static dashboard bundle at `/c/<token>`.**

## 2. Repo and environment

- Repo: `C:/Users/Abu/Documents/Python/CornerWork` (Windows). **No git remote existed as of 2026-09-28.** First action: `git init` if needed, commit, push to a private GitHub repo. Never work on an uncommitted tree.
- `extension-demo/`: the Chrome extension, v0.3.0, **installed in the user's Chrome**. Modify in place; do not scaffold a new extension.
- `demo/`: FastAPI + SQLite demo (`server.py`, `core.py`, `static/index.html`, port 8765). Becomes the backend. Its HTML is reference only.
- Node tests: `node extension-demo/test-core.cjs`, `test-gymdesk.cjs`, `test-background.cjs`. Keep green.
- Node fallback binary: `C:/Users/Abu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`; Python in sibling `dependencies/python/`. Check what's installed before adding tooling. Use UTF-8 when writing files. PowerShell sandbox commands sometimes need escalation.
- Secrets in `.env` (never committed): `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_NUMBER`, `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`, `PUBLIC_URL`, `BACKEND_URL`.

## 3. Data you must not lose

The user's installed extension holds real state in `chrome.storage.local` (`coachingState`, `gymdeskSnapshot`) including a reply "Thanks!" to the log "Class was OK, Abu is excellent", and 1 imported Gymdesk attendance row for Sarah Demo. **Before any change to storage or migration:** export it to `backup/chrome-storage-<date>.json` (ask the user to run the snippet in the extension's service-worker console if you can't reach Chrome), confirm the file has the reply, then proceed. Never clear storage without the user's explicit OK after the backend shows the migrated reply.

## 4. Gymdesk test account (fictional data, real trial)

Gym **AKLabs MMA**. Sarah Demo member `12672454` (attendance page `/manager/members/attendance/id/12672454`, row `62252846`, session `1832536`); Alex Demo `12672458` (no attendance, intentional); Maya Demo instructor `81192`. Class **Box** 2026-09-29 07:00–08:00. Gymdesk rejects future-dated check-ins; don't retry. No billing. Credentials are the user's; ask, don't guess. Gymdesk has no public API; import is DOM-reading in `gymdesk-reader.js`.

## 5. Decisions (settled, do not reopen)

| Topic | Decision |
|---|---|
| Athlete surface | SMS/RCS only (Twilio). WhatsApp later for UK. No app. |
| Staff surface | Dashboard bundle in three containers: extension tab, Gymdesk side panel, phone via magic link `/c/<token>` (PWA). One codebase. |
| Coach reply by texting `#name` | **Rejected.** |
| Embedded Gymdesk panel | Kept as quick view only; not primary. |
| State of record | Backend SQLite (SQLModel). Chrome storage = cache + Gymdesk snapshots + offline queue. |
| AI | Backend only: `parse_log` → `{summary, techniques[], sentiment, injury|null, concussion_flag, coach_draft}`; Whisper for audio; brief and recap generators. Never in the extension. |
| Video, CV, VLM | Out of scope. |
| Pricing (for copy/screens) | $25 add-on: $10 coach, $5 Cornerwork, $10 gym; or tiered flat $99/$249/$499. |
| Safety | No medical advice ever; concussion keywords → referral line + coach alert; adults only; JOIN/STOP; no marketing texts. |
| Integrations | Gymdesk via extension DOM import + CSV fallback. Mindbody deferred. Never single-sourced on Gymdesk markup. |
| Pilot gyms | Not MK (user trains there). |

## 6. Architecture

```
Athlete phone ──SMS/MMS──► Twilio ──webhook──► FastAPI backend (thin)
                                                 /sms · Whisper · parse_log · scheduler
                                                 SQLite: athletes, consents, messages, logs,
                                                 flags, replies, classes, bookings, briefs,
                                                 drills, events
                                                 /api/* JSON · /c/<token> static bundle
                                                        ▲               │
                       POST attendance/roster            │               │ JSON
Extension (desktop)                                      │   Phone (any browser)
  dashboard.html tab · Gymdesk side panel                │   same bundle at /c/<token>
  gymdesk-reader.js DOM import · chrome.storage cache    │   PWA, localStorage cache
        └────────── same components; adapter.js selects container ──────────┘
```

**Hard rule:** components under `extension-demo/components/` never reference the `chrome` global. All `chrome.*` lives in `background.js` and `adapter.extension.js`. Add an ESLint rule for it.

## 7. Build order (from 07-implementation-plan.md)

| Phase | Deliverable | Exit test |
|---|---|---|
| 0 | Git remote, storage backup, `.env.example`, **start 10DLC registration** | Remote exists; backup has "Thanks!" |
| 1 | Backend: spec tables, `/api/inbox`, `/api/brief/{class}/{date}`, `/api/replies`, `/api/import/attendance`, `/api/import/roster`, `/api/owner/summary`, bearer token, idempotent upsert, `scripts/migrate_chrome_state.py`, `/c/{token}` static route | `curl` inbox returns Sarah's log + reply |
| 2 | Extension: `adapter.js` (+ `.extension`, `.web`), `dashboard.html/js`, `components/{inbox,brief,owner}.js`, toolbar → tab, side panel → `#brief`, offline/stale bar, harness guard | Coach sees log, sends reply from tab, brief for Box renders |
| 3 | `parse_log` + schema + retry, run on every log, editable `coach_draft`, brief generator, safety post-check, 50-log eval | "shin sore after checks" → injury flag; "dizzy" → concussion flag |
| 4 | Twilio: tunnel, `/sms`, JOIN/STOP + consents, text log → inbox, outbound reply, MMS audio → Whisper | Text from test phone appears in extension in <10 s; reply lands |
| 5 | Phone: `/c/{token}` serves bundle with web adapter, PWA manifest + SW, brief-by-SMS with link, 390 px pass | Link opens dashboard on phone; Add to Home Screen works |
| 6 | Scheduler (after-class nudge, Sunday recap), Gymdesk roster import, owner early-warning | One nudge per athlete/day; real bookings in brief |
| 7 | Fly.io + nightly backup, Sentry, `DEMO_MODE`, consent copy, private extension distribution, metrics | Pilot definition of done |

Demo-ready after Phase 4. Do phases in order; each ends with tests green and a commit.

## 8. Existing extension files: keep / change

| File | Action |
|---|---|
| `manifest.json` | → 0.4.0; add `host_permissions` for backend URL |
| `gymdesk-reader.js` | Keep; generalize to any member page, then schedule/roster pages |
| `background.js` | Keep; add backend fetch proxy, snapshot POST, toolbar → `dashboard.html`, side panel on Gymdesk |
| `core.js` | Keep shapes/transitions; backend is source of truth |
| `gymdesk-bridge.js` | Keep; one more migration pass to backend |
| `gymdesk-embed.js`, `embedded.*` | Keep as quick view; re-point to shared components; verify in live Gymdesk |
| `panel.html/js` | Wrapper around `dashboard.html#brief`; delete old UI after |
| `index.html`, `lab.js`, `voice.js` | Test harness only, behind `?harness=1`; unlink from product |
| tests `*.cjs` | Keep and extend |
| **new** | `adapter.js`, `adapter.extension.js`, `adapter.web.js`, `dashboard.html`, `dashboard.js`, `components/`, `web/manifest.webmanifest`, `web/sw.js` |

## 9. LLM contract (`parse_log`)

Input: transcript + athlete goal + last 3 summaries. Output, validated with Pydantic, retry once:

```json
{"summary":"≤2 sentences","techniques":["jab exit angle"],"sentiment":"pos|neutral|neg",
 "injury":{"area":"left shin","severity":"minor|moderate|serious|unknown","quote":"..."},
 "concussion_flag":false,"coach_draft":"1–2 sentence suggested reply"}
```
Rules in prompt: never diagnose; never suggest training through pain; head/dizzy/blackout → `concussion_flag: true`; unknown → `null`, not guesses. Record `llm_model` and, on reply, the edit distance between `coach_draft` and what was sent (`events.reply_sent.meta.edit_distance`). This number is the pilot's key moat metric.

## 10. Events (all metrics come from here)

`opt_in, opt_out, log_received, log_parsed, injury_flagged, reply_sent, reply_read, nudge_sent, recap_sent, brief_generated, brief_opened, booking_imported, check_in`. Columns: `id, gym_id, athlete_id?, user_id?, type, meta json, at`. Never compute a dashboard number from anything else.

## 11. Working agreements with the user

- Short, concrete replies. State what you did, what's verified vs mocked, what's next. No repeated manual-step lists.
- Distinguish "verified in installed Chrome" from "passed in mocked preview." Say which.
- Ask a blocking question only if it changes the outcome; otherwise state the assumption and proceed.
- Never fabricate metrics on screens; label demo data.
- Commit after each phase with a message naming the phase.
- If you cannot reach the user's Chrome, say so; don't claim to have reloaded or inspected it.

## 12. First 60 minutes checklist

1. `git status` / init / commit / push. Confirm remote URL back to the user.
2. Ask the user to run the storage-export snippet (provide it) or confirm a backup exists.
3. Run the three `.cjs` tests; report results.
4. Read `demo/core.py` and `extension-demo/background.js` fully before changing either.
5. Start Phase 1.1 (schema) and 1.2 (`/api/inbox`) and stop for a short check-in with a `curl` transcript.

## 13. Out of scope for now

Mindbody, Stripe/billing, multi-gym auth beyond bearer tokens, anonymous feedback, Chrome Web Store public listing, video/CV, WhatsApp.
