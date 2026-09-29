# Cornerwork

Coaching between classes. Athletes text the gym number after training. The backend transcribes, summarizes and flags injuries. Coaches reply and read a pre-class brief in the Chrome extension or on a phone via a magic link. Owners see the numbers in the same dashboard.

Docs: `docs/08-agent-handoff.md` (decisions), `docs/07-implementation-plan.md` (phases), `docs/03-mvp-spec.md` (data model, LLM contract).

## Run the backend

```powershell
.\start.ps1            # frees port 8765, creates .venv/.env if missing, starts the backend, prints + copies the token, opens the dashboard
.\start.ps1 -Stop      # stop it
```

Manual equivalent:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # fill in keys; leave blank for offline fakes
.venv\Scripts\python.exe -m app.main          # http://127.0.0.1:8765  (set PORT to change)
.venv\Scripts\python.exe scripts\issue_token.py   # prints the gym API token
```

Fakes are used automatically when a key is missing: `ANTHROPIC_API_KEY` (parse/brief), `OPENAI_API_KEY` (voice transcription), `TWILIO_*` (SMS). `DEMO_MODE=1` forces all fakes.

## Load the extension

1. `chrome://extensions` > Load unpacked > `extension-demo` (or Reload if already installed).
2. Click the Cornerwork toolbar icon. The dashboard opens in a tab.
3. Settings > paste the backend URL and the token > Save and test.
4. On Sarah Demo's Gymdesk attendance page: Settings > Import attendance. The snapshot is posted to the backend.

Phone: open `http://<backend>/c/<token>` in any browser. Same dashboard, web adapter.

## Athletes on SMS (needs a Twilio number)

1. Put `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_NUMBER` in `.env`.
2. Expose the backend: `cloudflared tunnel --url http://127.0.0.1:8765` (or ngrok). Put the https URL in `PUBLIC_URL`.
3. In the Twilio console set the number's messaging webhook to `<PUBLIC_URL>/sms` (HTTP POST). Signatures are verified against `PUBLIC_URL + /sms`.
4. From a test phone: `JOIN` > `YES 18` > text or voice-note after class. Reply from the dashboard; the athlete receives `<COACH_NAME>: ...`.

10DLC registration is required before texting anyone but verified test numbers.

## Demo script (docs/04-demo-and-pilot.md)

1. Open the brief for the next class. Point at the flag and the focus line.
2. Hand over a phone: text the number.
3. Refresh the inbox: message, summary, tags, injury flag.
4. Send a one-line reply. It lands on the phone.
5. Back to the brief: the athlete is in it.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
node extension-demo\test-core.cjs; node extension-demo\test-gymdesk.cjs; node extension-demo\test-background.cjs
.venv\Scripts\python.exe scripts\eval.py          # parse_log acceptance proxy (add --live for Claude)
```

## Data

`data/cornerwork.sqlite3` is the store of record (gitignored). `backup/` holds the exported Chrome extension state; `scripts/migrate_chrome_state.py` imports it once, idempotently. All dashboard numbers derive from the `events` table.
