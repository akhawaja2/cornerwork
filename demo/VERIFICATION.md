# MVP demo verification

Date: 2026-09-28. Scope: lightweight local demonstration, grounded in the root MVP spec and demo runbook. Parallel backend, frontend and independent acceptance-test agents contributed; parent integrated and verified.

| Requirement | Implementation evidence | Verification |
|---|---|---|
| Small runnable implementation | core.py, server.py, static/index.html; local SQLite; no frontend build | Installed dependencies, launched server, health200 |
| Doc-grounded scope | DEMO.md scope table and open product choices | Compared PRD feature1–10 and runbook against implementation |
| Fictional seeded demo | core.seed:10athletes,14dayhistory,Thursday19:00bookings | Repeatable seed test and rendered brief |
| Consent/STOP/adults | inbound command flow, consents records, outbound gate | Tests for rawtext/time, adult confirmation, blocked reply/jobs |
| Text and simulated voice | inbound + add_log; deterministic parser | Transcript fidelity, injury and immediate coach-alert tests |
| Coaching loop | /api/inbound, /api/reply, inbox, simulated conversation | HTTP plus real browser end-to-end test |
| Explicit coach SMS targeting | registered coach phone, #athleteID reply | Ambiguous/missing target rejected, correct recipient verified |
| Context brief | booking-filtered brief with recent logs, flags, focus | Class/date membership tests and desktop/mobile visual inspection |
| Scheduled nudges | clock-controlled jobs, daily event keys, local quiet hours | 44min/45min boundary, no-show exclusion, quiet hours, rerun zero |
| Weekly recap | active participants, actual coach note, <=320 characters | Content/length and idempotency tests |
| Owner metrics | event-derived counts/timing, roster status, precise drift note | Handcomputed fixture arithmetic and browser rendering |
| CSV roster/bookings | validated transactional upserts | Repeat import, badphone, invalid second-row rollback, timezonecheckin |
| Confidential concerns | separate owner records; coach state suppresses content | Marker absent from coach payload, present in owner payload |
| Audit visibility | messages/events owner inspection | UI navigation verified |
| Mobile demo | responsive one-page UI | All five390px views no horizontal overflow or JSerrors |
| Handoff | DEMO.md, start-demo.ps1, screenshots | Files present and server left running withcleanseed |

Not claimed: real SMS/email delivery, real speech recognition or LLM output, secure multi-user authentication, production deployment, live booking integrations, payments, always-on scheduler, pilot legal/10DLC/monitoring/backup gates. These are expressly represented as simulations or deferred deployment work, rather than presented as completed production features. No actual customers contacted and no external messages sent.

Result: the requested local MVP demo is implemented and verified. Production/pilot readiness is a separate scope.
