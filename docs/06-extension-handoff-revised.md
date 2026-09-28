---
artifact_contract: "ce-handoff/v1"
created_at: "2026-09-28T22:10:00+00:00"
supersedes: "cornerwork-dashboard-handoff.md (2026-09-28T20:08Z)"
title: "Cornerwork: reconciled handoff — the Chrome extension is the coach/owner app"
summary: "Keeps every verified fact from the prior handoff. Direction fixed to the original design with one clarification from the user: the extension IS the app for coaches and owners (dashboard tab + side panel on Gymdesk). Athletes text. A thin backend receives SMS, runs the LLM and stores state; it has no UI of its own."
keywords: ["cornerwork", "gymdesk", "chrome-extension", "dashboard", "handoff", "sms"]
cwd: "C:/Users/Abu/Documents/Python/CornerWork"
resume_focus: "Build the extension's dashboard tab (inbox + pre-class brief + owner view) reading from a thin FastAPI backend; wire Twilio inbound to that backend; keep Gymdesk DOM import inside the extension."
---

# Cornerwork handoff (reconciled)

## 0. What changed and why

| Prior handoff | Decision now |
|---|---|
| Members submit questions/voice notes through an extension page | **Athletes text** the gym number (SMS/RCS via Twilio). The in-extension member simulator stays as a test harness only. |
| Coaching state lives only in `chrome.storage.local`; no backend | **Extension is the UI; a thin backend is the store.** Twilio can only deliver to a server, and the LLM needs a key that can't ship inside an extension. Chrome storage = cache + Gymdesk snapshots + offline queue. |
| No AI or transcription | Backend runs `parse_log` (summary, techniques, sentiment, injury flag, `coach_draft`) and Whisper. Extension shows results and lets the coach edit/send. |
| "Dedicated tab" vs embedded panel, hosting undecided | **Both, inside the extension:** a full dashboard tab (`chrome-extension://…/dashboard.html`) for coaches and owners, and the side panel / floating panel on Gymdesk pages for the quick pre-class glance. Same code, two containers. |

The designed loop is unchanged: after-class SMS nudge → athlete text/voice → AI summary + flags → **coach replies from the extension** → **pre-class brief in the extension** → weekly recap SMS. Pilot metrics come from the backend `events` table.

## 1. Latest user direction

The extension is the product for gym staff: after athletes text, coaches respond and view the pre-class brief in the extension. A business owner opens the dashboard tab and uses it as-is. User has ADHD, wants short concrete explanations and automation, and doesn't want repeated manual steps. Be honest about limits.

## 2. Product context (corrected)

- **Athlete:** SMS only. Never installs anything.
- **Coach:** the dashboard. Inbox (logs + AI summary + one-tap reply, edit `coach_draft`, attach a drill) and pre-class brief (who's booked, flags, themes, suggested focus). **Desktop = extension tab / Gymdesk side panel. Phone = the same dashboard bundle served by the backend at a magic link** (`/c/<token>`), installable to the home screen. One codebase, three containers.
- **Owner:** dashboard tab (extension on desktop, magic link on phone). Early warning, coached-tier count/revenue, coach reply times, feedback themes.
- **Not doing:** coach replies by texting the gym number with `#name` prefixes. Rejected as bad UX.
- **Gymdesk:** current integration via DOM import in the extension (no public API). Mindbody deferred.
- Pricing, safety rules, opt-in/STOP, adults only: per `01-business-case.md` / `04-demo-and-pilot.md`.

## 3. What exists, roles reassigned

| Component | Verified state | Role now |
|---|---|---|
| FastAPI + SQLite demo (`demo/server.py`, `demo/core.py`, port 8765) | Runs; has coach/owner HTML views; no auth; not connected to extension | **Backend only.** Keep the API and domain logic (`core.py`). Its HTML views are reference for the extension UI, then retired. |
| Chrome extension v0.3 (`extension-demo/`) | Real installed-Chrome DOM import of Sarah's attendance; local coaching flow; tests pass | **The app.** Gains a dashboard tab, talks to the backend, keeps Gymdesk import. |
| Embedded coach panel (`gymdesk-embed.js`, `embedded.*`) | Written; mocked preview only; not verified in live Gymdesk | **Kept as the on-Gymdesk quick view**, rendering the same components as the dashboard tab. Verify in live Gymdesk before relying on it. |

## 4. Verified facts (unchanged)

1. Real Gymdesk trial; user signed up/logged in.
2. Sarah Demo checked into **Cornerwork Test — Boxing**, 2026-09-28 07:00–08:00; attendance shows 1 session / 1 hour.
3. Extension v0.2 installed in the user's Chrome; screenshot shows 1 attendance record imported. Real installed-Chrome DOM import.
4. User submitted "Class was OK, Abu is excellent" and replied "Thanks!"; visible in installed extension and next-class brief.
5. Synthetic 0.5 s WAV queued, decoded, persisted with reply. Physical mic not verified.
6. v0.3 embedded UI rendered only in a mocked preview.
7. `test-core.cjs`, `test-gymdesk.cjs`, `test-background.cjs` pass; syntax checks pass.

Not built/verified: SMS/email, production API, account-wide sync, roster import, transcription, AI, deployment, billing, shared staff login.

## 5. Gymdesk test records (unchanged)

Gym **AKLabs MMA**. Sarah Demo `12672454` (attendance `/manager/members/attendance/id/12672454`); Alex Demo `12672458` (no attendance, intentional); Maya Demo instructor `81192` (no staff login). Sarah row `62252846`, session `1832536`. **Box** class 2026-09-29 07:00–08:00 exists; Gymdesk rejects future-dated check-ins. No paid memberships, no billing. No credentials here. `GYMDESK-TEST.md` older notes superseded.

## 6. Extension internals: keep / change

`manifest.json` 0.3.0; permissions `sidePanel`, `activeTab`, `scripting`, `storage`; content script on `https://app.gymdesk.com/manager/*`.

| File | Keep / change |
|---|---|
| `gymdesk-reader.js` | Keep. Generalize from Sarah's URL to any member page, then to class schedule/roster pages. |
| `core.js` | Keep state transitions; source of truth moves to backend. |
| `background.js` | Keep capture. Add: `fetch` to backend API (`/api/import/attendance`, `/api/logs`, `/api/replies`, `/api/brief`), auth token from `chrome.storage`, toolbar click → open `dashboard.html` in a tab; on Gymdesk pages also open side panel. |
| `gymdesk-bridge.js` | Keep migration; after slice B, coaching state syncs from backend, not localStorage. |
| `gymdesk-embed.js`, `embedded.*` | Keep as quick view; import shared components from the dashboard; verify in live Gymdesk. |
| `panel.html/js` | Fold into `dashboard.html`; remove after. |
| `index.html`, `lab.js`, `voice.js` | Test harness only. Add `?harness=1` guard; never linked from product UI. |
| **new** `dashboard.html`, `dashboard.js`, `components/` (inbox, brief, owner) | The product UI. **Plain HTML/JS, no extension-only APIs in the components** (all `chrome.*` calls isolated in `background.js` / a thin adapter) so the identical bundle runs as a web page. Must render with the backend down (cached snapshot, marked stale). |
| **new** `adapter.js` | Two implementations of the same interface: `extension` (uses `chrome.storage`, `chrome.runtime` messaging) and `web` (uses `fetch` + `localStorage`). Dashboard imports the adapter, never `chrome.*` directly. |
| **new** `manifest.webmanifest`, `sw.js` (web build only) | Home-screen install + offline shell for the phone version. Served by the backend, not part of the extension package. |

Storage keys unchanged (`coachingState`, `gymdeskSnapshot`, `gymdeskError`, legacy `cornerwork-extension-fictional-v1`, marker `cornerwork-shared-migrated`). `coachingState` becomes a cache of backend state plus an offline write queue.

**Preserve the user's Chrome data.** The "Thanks!" reply is in the installed extension's storage. Migration = read installed `chrome.storage.local` → POST to backend once → confirm with user → then clear. Unconfirmed v0.3 localStorage migration still applies.

## 7. Target architecture

```
Athlete phone ──SMS/MMS──► Twilio ──webhook──► Backend (FastAPI, thin)
                                                 • /sms: JOIN/STOP, log intake
                                                 • Whisper + parse_log (LLM)
                                                 • SQLite: athletes, logs, flags,
                                                   replies, classes, bookings,
                                                   briefs, events
                                                 • /api/* JSON for the extension
                                                 • scheduler: nudges, recaps, briefs
                                                        ▲            │
                          POST attendance/roster        │            │ JSON
                                                        │            ▼
Chrome extension (desktop)                 Phone (any browser)
  • dashboard.html tab                       • same dashboard bundle at
  • side panel on Gymdesk pages                https://…/c/<token> (magic link)
  • gymdesk-reader: DOM import               • home-screen install (PWA)
  • chrome.storage: cache + offline queue     • localStorage cache
        └──────── same components, adapter.js picks the container ────────┘
```

Why the backend can't be zero: Twilio must POST to a public URL; scheduled nudges must fire when Chrome is closed; the LLM key must not ship in an extension. Backend serves **one static route** (`/c/<token>` → the dashboard bundle) and JSON; nothing else user-facing. Pilot: localhost + an ngrok/Cloudflare tunnel for Twilio and for phones. Later: Fly.io.

## 8. Decisions taken

| Open before | Decision |
|---|---|
| Where the coach/owner UI lives | **The dashboard bundle**: extension tab + Gymdesk side panel on desktop; magic-link web/PWA on phones. Same code. |
| Coach on a phone | Magic-link dashboard. **Not** SMS `#name` replies (rejected). |
| Where state lives | Backend SQLite; extension caches. |
| Athlete surface | SMS via Twilio. Simulator = harness. |
| Upcoming-classes section | Real bookings from Gymdesk roster import; else labeled "demo data". No fabricated metrics. |
| Auth | Extension holds a per-gym API token (magic-link issued) in `chrome.storage`. Not needed on single-machine localhost. |
| Hosting | Localhost + tunnel for pilot; Fly.io after 3 gyms. |

## 9. Continuation plan (build order)

| # | Slice | Done when |
|---|---|---|
| A | Backend `/api/import/attendance` + extension POSTs `gymdeskSnapshot`; upsert athletes by Gymdesk member ID | Sarah's record in backend DB; re-import idempotent |
| B | One-time migration of installed coaching state ("Thanks!") → `logs`/`replies` | Reply visible in dashboard; user confirmed; old storage cleared |
| C | `dashboard.html` tab: **inbox** (logs, summary placeholder, reply box) + **brief** for Box 09-29 from imported attendance; toolbar opens it. Components use `adapter.js`, never `chrome.*` | Coach sees Sarah's log/reply and the brief from the extension tab |
| C2 | **Phone version**: backend serves the same bundle at `/c/<token>` with the `web` adapter; magic link sent by SMS; PWA manifest + service worker; brief pushed as an SMS with the link 90 min before class | Coach opens the link on a phone, sees the same inbox and brief, sends a reply; works after "Add to Home Screen" |
| D | Backend `parse_log` (LLM) on every log; inbox shows summary, tags, injury flag, editable `coach_draft` | "Class was OK, Abu is excellent" → summary + sentiment; injury sentence → flag |
| E | Twilio inbound `/sms` (JOIN/STOP, text log) via tunnel; outbound reply from the inbox | A text from a test phone appears in the extension inbox; reply lands on the phone |
| F | Gymdesk **schedule/roster** import in `gymdesk-reader.js`; brief keyed to real bookings | "Demo data" label gone; brief lists booked athletes |
| G | Side panel on Gymdesk class page shows the brief for the class on screen (verify in live Gymdesk) | Coach opens a class in Gymdesk, panel shows that class's brief |
| H | Owner view in dashboard: early warning, coached count, reply times, from `events` | Numbers match fixtures |
| I | Voice note via Twilio media → Whisper → same pipeline; retire `voice.js` from product path | MMS audio → transcript → log |
| J | After-class nudge + Sunday recap scheduler on the backend | Nudge sent 45 min after a booked class; one per athlete/day |

Deferred: Mindbody, Stripe/billing, multi-gym auth beyond tokens, anonymous feedback, Chrome Web Store listing (unlisted/private distribution for pilot gyms is fine).

## 10. Acceptance evidence

Preserve the existing reply · read actual imported attendance · submit and reply to a message from the extension · same history in dashboard tab and side panel · empty/unsupported ≠ fabricated · verify installed Chrome separately from mocks · **one log arrives by real SMS · one `coach_draft` edited and sent from the extension · `events` rows for `log_received`, `reply_sent`, `brief_generated`.**

## 11. Honest limitations

- Gymdesk import is DOM-scraping; breaks when their markup changes; only runs while Chrome is open. Backend scheduler covers nudges/recaps regardless.
- Chrome on phones can't run extensions; the magic-link PWA (slice C2) is the phone path. Keep the dashboard free of `chrome.*` calls or the phone build breaks. Push notifications on iOS require the PWA to be installed to the home screen; until then the 90-min brief arrives as an SMS containing the link.
- A magic link is a bearer credential: expire tokens (30 days), rotate on request, and never put athlete data in the URL.
- Concurrent writers to Chrome storage aren't production-safe; backend as source of truth fixes it.
- No commit/branch/remote exists. **First action: `git init`, commit, push.**
- 10DLC registration not started; needed before texting anyone but test phones.
- Chrome Web Store review (if ever public) will ask about the Gymdesk content script and data handling; keep a written data-use statement.

## 12. Local commands (unchanged)

```powershell
.\extension-demo\start-preview.ps1
.\start-demo.ps1
node extension-demo/test-core.cjs
node extension-demo/test-gymdesk.cjs
node extension-demo/test-background.cjs
```

Node fallback `C:/Users/Abu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe`; Python in sibling `dependencies/python/`. UTF-8 when editing. Check the environment before reinstalling.

## 13. References

`03-mvp-spec.md` (data model, LLM contract; UI layer now = extension) · `04-demo-and-pilot.md` · `01-business-case.md` · `DEMO.md` · `extension-demo/README.md` (v0.3 section) · proof images in `extension-demo/` (note which are simulated).
