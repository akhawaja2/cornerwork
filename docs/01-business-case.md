# 01 — Business case

## The idea
B2B software for combat-sports gyms (then any skill sport). Athletes text or voice-note a gym number after class. AI transcribes, summarizes, tags techniques and flags injuries. The coach replies (voice or text) with a drill. Coaches get a pre-class brief (who's booked, flags, themes, suggested focus). Owners get early-warning signals and a new revenue line: a **"Coached" add-on** sold to members.

Sport-agnostic by design; launch in combat sports where the founder's credibility (nationally ranked Muay Thai, 9-1-1; ~10 yrs Muay Thai/BJJ/wrestling; senior software engineer) opens doors.

## Pricing — Option B (chosen)
Every $25 add-on: **$5 Cornerwork · $10 coach · $10 gym.** No base fee, no contract. Gym bills the add-on through its own software; Cornerwork invoices the gym monthly; coaches paid via gym payroll.

Why B over a flat fee: owner risk is zero ("nothing until you earn"), revenue grows with usage (NRR > 100% built in), one-sentence pitch. Trade-off: revenue depends on opt-in rate. If founding gyms average < 20 coached members, move to hybrid ($29 + $4/member) or add a $29 minimum after month 3.

Coach economics at 50/50: 15 coached members ≈ $150/mo for ~1 hr/week ≈ $35–50/hr (target; AI-drafted replies are what keep the hour at one).

## Unit economics (estimates)
| | Per gym |
|---|---|
| Revenue (15 coached, typical assumption) | ~$75/mo |
| Cost to serve (~$7 fixed + ~$1.25/member: SMS, transcription, LLM) | ~$26/mo |
| Gross margin | ~65–80% |
| SMB SaaS churn benchmark | 3–5%/mo |
| Gym lifetime value (~$49 profit/mo ÷ 4%) | ~$1,200–1,700 |
| Max cost to win a gym (3:1) | ~$400–550 → founder-led + referrals only, no paid ads |

**Company milestones (Option B, 15 coached/gym):** ~9 gyms covers fixed costs; ~110 gyms ≈ $5k/mo profit; ~315 gyms ≈ $15k/mo.

## Market
- 76,364 US martial-arts studios, +6% in 2026; $21.2B, 3.7% CAGR (IBISWorld via Gymdesk)
- 6.61M US participants (+4%), 3.13M core; ~750k BJJ. Boxing/MMA *for fitness* down 14% — casual cardio shrinking, serious training growing
- Serviceable: adult-focused combat gyms ≈ **10–15k** (assumption) → **~$11–17M/yr** max US revenue at ~$95/gym. Not venture-scale alone; becomes so only across skill sports + UK
- Demand evidence: BJJ Notes 30k+ users (athletes already self-log); many Amazon BJJ journals; Grappling AI (voice-note logging, $3.99/mo); coaches pay ~$130/mo for Trainerize/TrueCoach; gyms spend $535–977/mo on software

## Why members stay / leave (sourced)
- Retention drivers: friendly staff 31%, community 20%, accountability 17% (Sogolytics n=1,069)
- Cancel reasons: cost 41% (YouGov) → keep the add-on optional, never raise base price
- 12+ check-ins/mo ≈ 2% cancel risk vs ~20% at 1/mo; risk months 3, 6–7, 12 (PushPress)
- 81% of BJJ athletes injured/yr, ~34 days lost per injury (PMC n=881); NCAA wrestling 9.28 injuries/1,000 exposures, 31% of HS competition injuries = 3+ weeks out

## Competitors
| Who | Good at | Doesn't do |
|---|---|---|
| Gymdesk / PushPress / Wodify / Mindbody | Billing, bookings, absence alerts (after attendance drops) | Coaching between classes; why they stopped |
| Mindbody Messenger[ai] | AI front desk, sales follow-ups | Training feedback |
| Trainerize / TrueCoach / Everfit | Online PT programming | A gym floor of 100+ |
| BJJ Notes / Grappling AI | Athlete self-logging | Anything for coach or gym |
| Skillest / CoachNow | Video coaching (golf) | Combat, gym rosters |

Differentiation: the only product combining athlete logs + coach reply + class brief + paid tier. Defensibility is low-to-moderate (any of the above could copy); defenses are speed, founding gyms, integrations, founder credibility, and log data. Window ≈ 12–24 months.

## Top risks
1. Capital One employment/IP terms — check first
2. Coach follow-through and pay (the operational make-or-break)
3. Owner willingness to pay (unproven — 0 interviews, 0 LOIs as of writing)
4. TCPA consent ($500–1,500 per unwanted text); opt-in only, STOP, consent log
5. Logging habit fades — nudges tied to check-ins, coach reply as the reward
6. Gym software adds a coaching loop — move fast, stay integrable/acquirable
7. Health-adjacent data (injury notes) — consent, deletion, security; not HIPAA but state laws apply
8. Founder time (full-time job + twice-daily training) — cap at ~10 hrs/week

## Verdict
Worth a **capped, bootstrapped 90-day bet**. Don't raise, don't quit. Kill by day 90 if: < 15 interviews show the pain, < 3 owners commit to a pilot, < 5% of members buy the add-on, or coaches reply < 50% of the time.

## Sources
Gymdesk industry stats · Gymdesk software cost guide · Gymdesk automations docs · PushPress retention guide · Athletech (Sogolytics, YouGov) · PMC BJJ injury study · PMC wrestling surveillance · Grips Intelligence (BJJ Fanatics) · Optifai churn benchmarks · a16z "Fintech scales vertical SaaS" · Skillest · Assistant Coach pricing comparison · Message Central (WhatsApp US pricing) · Twilio pricing · Stripe Connect pricing · Mindbody developer docs · BJJ Notes / AppBrain · Apple Messages for Business FAQ · DemandSage (US iOS share)
