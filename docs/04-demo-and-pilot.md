# 04 — Demo script & concierge pilot runbook

## Demo levels
| Level | What | Effort | Use for |
|---|---|---|---|
| 1 | Design canvas + deck | 0 | First interviews |
| 2 | Live-wire demo (slices 0–5 of the spec) | ~3½ days | Owner meetings |
| 3 | Concierge pilot (slices 6–11) | +4 days | Founding gyms |

## 3-minute meeting demo
1. Open the coach brief for "Thursday 7pm" on the seeded roster. Point at the injury flag and the suggested focus. *(30s)*
2. Hand over a phone: "Text this number like you just finished class." Voice note or text. *(30s)*
3. Refresh the inbox: their message, the AI summary, tags, injury flag if mentioned. *(30s)*
4. Type a one-line coach reply, send — it lands on their phone. *(30s)*
5. Back to the brief: their name is now in it. "That's the whole product. Your coaches do step 4, once a week, for $10 a member." *(60s)*

If the network fails: `DEMO_MODE=1` runs the seeded brief and a canned inbound offline. Nothing dies.

## Concierge pilot (before software): boxing coach + 5–8 athletes
**Setup (day 0)**
- Second phone line on an iPhone (real iMessage for the pilot only)
- Athletes opt in by texting `JOIN` first (consent text names the gym and Cornerwork; reply STOP anytime; 18+)
- Spreadsheet = the `events` table: `athlete · event · timestamp · source`
- Export the coach's athletes' attendance for the last 8–12 weeks if any system exists

**Daily (you, ~20 min)**
- After each class: send the nudge ("Good session? Voice note or text: what clicked, anything sore?")
- Run each log through the `parse_log` prompt by hand; paste the summary + draft reply to the coach
- Log `log_received`, `injury_flagged`, `nudge_sent`

**Coach (~1 hr/week)**
- Reply to each log within 48h by voice note (you transcribe and forward as text) — log `reply_sent` with timestamp
- Thursday: you send the pre-class brief (built by hand with the `class_brief` prompt)

**Weekly (Sunday)**
- Send each athlete a 3-line recap (`weekly_recap` prompt)
- Compute: % logging this week, median reply hours, coach minutes (ask the coach)

**Week 4 review:** compare against Gate 2 in `02-validation-plan.md`.

## Safety rules (apply in the pilot exactly as in the product)
- No medical advice, ever. Injury → "Flagged to Coach X. If it's serious, please see a medical professional."
- Concussion/head/dizzy/blackout keywords → same line, stronger, plus immediate coach alert
- Adults only; no marketing texts; STOP honored immediately and logged
- Confidential concerns (harassment, coach conduct): route to a named gym contact, not the coach; AI acknowledges and routes only
- Delete an athlete's data on request within 7 days

## What to record for the deck
- One real quote from a coach or athlete for the "gap" slide
- The actual opt-in %, logging %, reply time — replace the "typical" row on the math slide
- Before/after attendance for pilot athletes
