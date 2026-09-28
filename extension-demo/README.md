# Cornerwork Gymdesk pilot — v0.2.0

## Try it in the installed Chrome extension

1. Open `chrome://extensions` and click **Reload** on Cornerwork. The existing unpacked folder is `extension-demo`.
2. Open https://app.gymdesk.com/manager/members/attendance/id/12672454 while logged in to AKLabs MMA.
3. Click the pinned Cornerwork icon. It opens the sidebar and reads Sarah Demo's saved attendance from that page.
4. The connection box should show a last-read timestamp and one attendance record. Select **Gymdesk — imported attendance** if necessary.
5. Click **Open member simulator** in the sidebar. This opens the extension's own Options page, which shares storage with its sidebar. Do not use localhost for this test.
6. Sarah's completed class unlocks a local post-class prompt. Record a voice note (up to 45 seconds), or upload an audio file (max 800 KB), and send it.
7. Return to the sidebar: **Reply queue** → reply → **Next class**. The reply also appears in the member simulator.

After saving another check-in, reload Sarah's Gymdesk Attendance page and click the toolbar icon again. **Refresh attendance** also works while the authorized Gymdesk tab is active.

## What is connected

The extension reads rendered, saved attendance rows for Sarah Demo (member 12672454) at AKLabs MMA. It uses Chrome's temporary `activeTab` access plus `scripting`; there are no permanent host permissions, hidden API requests, account credentials, Gymdesk writes, or account-wide sync. `storage` carries the attendance snapshot from the worker to the extension UI. Messages and audio stay in local extension storage.

This is an intentionally bounded pilot for this test member. It is not a general Gymdesk API integration. Gymdesk HTML changes may require updating the reader. Only rows loaded on the open attendance page are read. It does not watch all check-ins in the background.

Imported data is isolated from the two fictional scenarios. Completed class imports unlock a **local simulated prompt**, not an SMS/email. Class time is interpreted in the computer's timezone; match it to the gym timezone. If a class has not ended, refresh the import after its end. The next-class view summarizes coaching history; it does not import future bookings. No transcription or AI is included.

## Validation

- `node test-core.cjs`: existing voice/queue/provider regression tests.
- `node test-gymdesk.cjs`: class-end gate, import identity and date validation, idempotency, attendance association, removal, voice/reply preservation and provider isolation.
- `node test-background.cjs`: worker routing and Chrome API mock tests. These do not prove installed Chrome permission behavior.
- `connector-test.html` in the local preview runs the actual reader on minimal DOM captured from Sarah's saved Gymdesk attendance, then populates the local preview. This is a regression fixture, not live browser access.
- Browser-tested: saved DOM import → audio upload → coach queue → reply → next-class brief. Audio test uses a synthetic WAV. Physical microphone and the updated installed Chrome extension still require a manual check.

Local preview: run `start-preview.ps1`, then open http://127.0.0.1:8766/. HTTP preview and installed extension storage are separate.

Chrome permission reference: https://developer.chrome.com/docs/extensions/develop/concepts/activeTab


## v0.3 — embedded Gymdesk coach panel

Reload Cornerwork at chrome://extensions. Reload the extension member test page once to migrate existing local replies into shared extension storage. Refresh the Gymdesk tab. A floating **Cornerwork** button now opens the coaching panel inside the page. The toolbar icon opens this embedded panel too.

The new declared site access is limited to `https://app.gymdesk.com/manager/*`. Chrome may require enabling the updated extension/site access. It inserts an isolated panel and reads attendance only on request. It does not modify Gymdesk records.

Sarah's member pages show her queue, audio and replies. Schedule pages open her preparation brief; this pilot does not infer who is booked into a selected class. Other member pages explicitly show that they are unsupported rather than displaying Sarah's history. Closing the panel leaves Gymdesk usable. Member submission remains a separate test page.

Storage: existing Options/side-panel coaching histories migrate once to chrome.storage.local. The embedded frame uses this shared store; it does not depend on third-party iframe localStorage. The coach reply API uses the imported Gymdesk scenario only.

Validation: existing regression suites pass; local simulated-Chrome preview renders saved voice notes/replies and suppresses Sarah's history for unsupported members. Actual page injection and Gymdesk's iframe policy require the refreshed installed-Chrome test. The local preview is not proof of installed extension behavior.
