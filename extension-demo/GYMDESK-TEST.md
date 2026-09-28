# Gymdesk trial setup — 28 September 2026

Account: AKLabs MMA. Trial confirmed active (30 days displayed). Mindbody deferred by user.

Created and verified through Gymdesk's UI:

- Sarah Demo, member ID 12672454: https://app.gymdesk.com/manager/members/profile/id/12672454
- Alex Demo, member ID 12672458: https://app.gymdesk.com/manager/members/profile/id/12672458
- Maya Demo, instructor ID 81192: https://app.gymdesk.com/manager/gym/editstaff/id/81192

The fictional members have no contact information; account access emails were disabled. Maya is an instructor record with no login invitation and no account permissions. The existing owner account is used for the test. No payments or paid plan were configured.

Next: create a Cornerwork Test boxing class with Maya, register Sarah and Alex, check Sarah in while leaving Alex absent, then compare the real attendance state with Cornerwork's local voice-note flow. The schedule's Add Session control did not respond to automation; the user was asked to open the editor. No session has been created yet.

The local extension prototype currently uses fictional local state. It does not read Gymdesk attendance automatically. Native Chrome installation, live page context matching and attendance-event transport remain separate unverified steps.

## Verified September 28, 2026
Created a separate Cornerwork Test — Boxing session for September 28, 7–8am. Sarah Demo attendance saved and verified after reload: 1 session, 1 hour. September 29 Box class retained. Gymdesk rejects future-date attendance. Local Gymdesk demo preview has simulated ping, Sarah question, coach response, and next-class context; it remains independent of live Gymdesk and installed Chrome extension storage. Proof: sarah-attendance-proof.png.

