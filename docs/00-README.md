# Cornerwork — project docs

Working name: **Cornerwork** (placeholder; run a trademark search before using publicly).
One-liner: *Your coach, between classes.* Athletes text a gym number after training; AI summarizes and flags; the coach replies by voice; the gym sells it as a "Coached" add-on.

| # | File | What it is |
|---|---|---|
| 01 | `01-business-case.md` | The idea, pricing (Option B), unit economics, market, competitors, risks, verdict |
| 02 | `02-validation-plan.md` | 90-day gates, metrics, interview script, Facebook post, outreach lines |
| 03 | `03-mvp-spec.md` | PRD, tech stack, folder structure, data model, vertical slices, LLM contract |
| 04 | `04-demo-and-pilot.md` | 3-minute meeting demo script, concierge pilot runbook, safety rules |

## Deck and designs (exported into this folder)
| File | What |
|---|---|
| `cornerwork-pitch-deck.pdf` | 16-slide deck, vector PDF (text selectable) |
| `cornerwork-pitch-deck.pptx` | Same deck as PowerPoint (one full-bleed image per slide; edit the live version, then re-export) |
| `deck-slides/*.png` | Each slide as a 1920×1080 image |
| `cornerwork-design-canvas.pdf` | All 7 design boards, one per page |
| `design-canvas/*.png` | Coach brief, owner dashboard, athlete thread, progress page, architecture, QR poster, join page (2× resolution) |

Live, editable versions (private until shared):
- Pitch deck: https://claude.ai/artifact/8ZFAfcQFazMrRBp81axfYC
- Design canvas: https://claude.ai/artifact/UmY6wPVSmRDiRFq1PeR3wf

Exported 2026-09-27 from deck v6 and canvas v6. Speaker notes are not in the PDF/PPTX; they're in the live deck.

## Decisions log
| Date | Decision |
|---|---|
| 2026-09-27 | Freeze StrikeStats as a product; keep as a future video add-on |
| 2026-09-27 | No computer vision in MVP; optional VLM clip hints later, coach-only |
| 2026-09-27 | No video at launch (until WhatsApp channel exists) |
| 2026-09-27 | SMS/RCS first (US Northeast, iPhone-heavy); WhatsApp later for UK |
| 2026-09-27 | Pricing Option B: $5 of every $25 add-on, no base fee; hybrid after pilot if avg coached < 20 |
| 2026-09-27 | Coach split default 50/50 of the remaining $20 ($10 coach / $10 gym) |
| 2026-09-27 | Do not pilot at MK (protect athlete relationship); pilot with boxing coach + 2–3 outside gyms |
| 2026-09-27 | Adults only at launch |

## Before anything else
1. Check Capital One side-work and IP policy.
2. Trademark search on the name.
3. Start 10DLC (business texting) registration — takes days.
