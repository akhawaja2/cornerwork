# Cornerwork demo presenter guide

Use `cornerwork-demo-flow-v2.pptx` (editable text and embedded screenshots) or the companion PDF. This is a new demo edition of the original raster pitch deck, retaining its cream/charcoal/teal palette and 16:9 dimensions. The original pitch files remain available. All ten slides contain presenter notes. Slide 10 is an optional technical appendix: supporting both systems is feasible, but reliable syncing, approved access and ongoing maintenance are the main work.

## Five-minute presentation

- Slides 1–2 / 30 seconds: Explain the class-to-class coaching loop and state that this is a fictional local prototype.
- Slide 3 / 40 seconds: Open Demo tools. Select a seeded active athlete such as Maya Chen. Choose After class, then Run due jobs. Inspect the simulated conversation. This only advances the job runner, not all app clocks. If a previous run already sent the nudge, the duplicate is intentionally suppressed; show the recorded message. Do not reset an existing demo without first deciding its changes are disposable.
- Slide 4 / 45 seconds: Choose the voice-note typed-transcript option. Enter: “My jab felt sharper, but I keep getting countered as I step out. What should I focus on next class?” Send into demo. Explain that real recording and transcription are not connected.
- Slide 5 / 60 seconds: Open Coach inbox. Find the new log, read the original, and write a reply such as: “Let's look at your exit together before the next round. Remind me before class and we'll work through it.” Send and show the simulated conversation in Demo tools.
- Slide 6 / 45 seconds: Open Before class and refresh the class the same athlete is booked into. Show the new context among recent logs. This demonstrates recent feedback appearing, not a verified record that the coach performed a follow-up.
- Slides 7–8 / 30 seconds: Explain the proposed live test and remaining integration boundaries. Avoid a technical walkthrough unless asked.
- Slide 9 / discussion: Ask who would own the queue, how they handle this today, and what would make a paid pilot worthwhile.

## Rehearsal checks

Open http://127.0.0.1:8765 and confirm the app is running. Choose a fictional, active, opted-in athlete already booked into the displayed class. The current scheduler accepts booked or attended records; attendance-only triggering is a required change before representing a live integration. A submitted log does not add a booking. Recent context uses the last seven days against the app's actual clock, so old fixtures may need refreshing for a later presentation.

No real SMS, microphone capture, speech recognition, LLM, provider connection or staff authentication is active. The anonymous dashboard is outside this presentation. The existing owner overview is not evidence of an anonymous reporting product.

## Real Gymdesk pilot test

Use a cooperating gym's authorized connection and dedicated opted-in adult test account. [Gymdesk's Zapier documentation](https://docs.gymdesk.com/en/help/docs/zapier) lists Check-In plus booking/attendance searches. First verify the actual payload and whether class end can be resolved. Do not assume a booking or a generic facility check-in proves attendance in a specific class.

Book a test class, mark attendance, verify exactly one follow-up after the chosen delay, submit a real text/audio sample through the selected delivery channel, have the coach reply, then book the next class and check the brief. Repeat for cancellation, no-show, duplicate event, opt-out and timezone boundary. Pass means correct recipient, correct class, one delivery, recorded coach reply, and fresh context in the next brief. Reconcile provider delivery receipts; a local outbox row is not delivery evidence.

## Mindbody follow-on

[Mindbody webhook documentation](https://developers.mindbodyonline.com/WebhooksDocumentation) describes roster events and signed-in status. Verify developer access, gym authorization, class/member identifiers and event payloads before adopting the integration. A working API sandbox does not prove production webhook access. Run the same acceptance sequence independently; do not infer Mindbody works because Gymdesk does.

## Pricing discussion

The current $50–100/gym/month idea is a hypothesis, not a committed offer. Ask about willingness to pay after discussing the present workflow. Optional $10/member resale needs a separate test and allowance for coach labor. Do not use the old revenue-split promise or claim proven retention improvement.
