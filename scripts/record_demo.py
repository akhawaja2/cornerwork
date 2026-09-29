"""Record the 5-step demo (docs/04-demo-and-pilot.md) as a video against a throwaway backend.
Usage: .venv/Scripts/python.exe scripts/record_demo.py  -> demo-materials/cornerwork-demo-<date>.mp4
Needs: playwright (pip), Chromium from Playwright, ffmpeg on PATH. Everything runs offline with the fakes."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PORT = 8778
BASE = f"http://127.0.0.1:{PORT}"
OUT = ROOT / "demo-materials" / f"cornerwork-demo-{date.today().isoformat()}.mp4"
PHONE = "+15550000001"
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
PY = ROOT / ".venv" / "Scripts" / "python.exe"

CAPTION_JS = """(text) => {
  let el = document.getElementById('cw-caption');
  if (!el) { el = document.createElement('div'); el.id = 'cw-caption';
    el.style.cssText = 'position:fixed;left:0;right:0;bottom:0;padding:16px 24px;background:#203d36;color:#fff;font:600 20px/1.3 system-ui;z-index:9999;box-shadow:0 -2px 12px rgba(0,0,0,.2)';
    document.body.appendChild(el); }
  el.textContent = text;
}"""


def post_sms(body, **extra):
    data = urllib.parse.urlencode({"From": PHONE, "To": "+15550000000", "MessageSid": f"SM{int(time.time()*1000)}", "NumMedia": "0", "Body": body, **extra}).encode()
    with urllib.request.urlopen(urllib.request.Request(f"{BASE}/sms", data=data)) as r:
        return r.read().decode()


def api(token, method, path, payload=None):
    req = urllib.request.Request(f"{BASE}{path}", method=method, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                 data=json.dumps(payload).encode() if payload else None)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def main():
    work = Path(tempfile.mkdtemp(prefix="cw-demo-"))
    db = work / "demo.sqlite3"
    env = {**os.environ, "DEMO_MODE": "1", "PORT": str(PORT), "CORNERWORK_DB": str(db), "CORNERWORK_MEDIA": str(work / "media"), "COACH_NAME": "Coach Abu"}
    for key in ("TWILIO_AUTH_TOKEN", "PUBLIC_URL"):
        env.pop(key, None)
    # Seed: Sarah's real migrated log + reply, so the inbox is not empty on frame one.
    subprocess.run([str(PY), "scripts/migrate_chrome_state.py", "backup/chrome-localstorage-2026-09-28.json"], cwd=ROOT, env=env, check=True, capture_output=True)
    subprocess.run([str(PY), "scripts/parse_missing.py"], cwd=ROOT, env=env, check=True, capture_output=True)
    token = subprocess.run([str(PY), "scripts/issue_token.py"], cwd=ROOT, env=env, check=True, capture_output=True, text=True).stdout.strip()
    server = subprocess.Popen([str(PY), "-m", "app.main"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{BASE}/health", timeout=1)
                break
            except Exception:
                time.sleep(0.25)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 800}, record_video_dir=str(work / "video"), record_video_size={"width": 1280, "height": 800})
            page = ctx.new_page()
            caption = lambda text: page.evaluate(CAPTION_JS, text)
            url = f"{BASE}/c/{token}"

            page.goto(url + "#brief")
            page.wait_for_selector("#cls")
            caption("1 · Before class: the coach opens the brief. Sarah Demo checked in via Gymdesk; her last log is here.")
            page.wait_for_timeout(3500)

            page.goto(url + "#inbox")
            page.wait_for_selector("article.card")
            caption("2 · An athlete texts the gym number after class: JOIN → YES 18 → their log.")
            page.wait_for_timeout(2000)
            post_sms("JOIN")
            post_sms("YES 18")
            post_sms("Sparring was great today, finally landing the cross. Left shin is sore after checks though.")
            api(token, "POST", "/api/import/roster", {"source": "manual", "athletes": [{"name": "Demo Athlete", "phone": PHONE}],
                                                       "bookings": [{"class_name": "Cornerwork Test — Boxing", "class_date": TOMORROW, "status": "booked", "phone": PHONE}]})
            page.reload()
            page.wait_for_selector("form[data-log]")
            caption("3 · Inbox: the text lands with an AI summary, technique tags, an injury flag and a draft reply.")
            page.wait_for_timeout(4000)

            caption("4 · The coach edits the draft and sends. The athlete gets it as an SMS. Edit distance is recorded.")
            box = page.locator("form[data-log] textarea").first
            box.click()
            box.fill("")
            box.type("Nice cross! Skip shin checks Tuesday, ice it tonight, and tell me how it feels before class.", delay=28)
            page.wait_for_timeout(600)
            page.locator("form[data-log] button").first.click()
            page.wait_for_selector("text=Reply saved.")
            page.wait_for_timeout(3000)

            page.goto(url + "#brief")
            page.wait_for_selector("#date")
            page.fill("#date", TOMORROW)
            page.dispatch_event("#date", "change")
            page.wait_for_selector("text=Demo Athlete")
            caption("5 · Back to the brief: the athlete is in tomorrow's class with the flag, a focus line and a note.")
            page.wait_for_timeout(4500)

            page.goto(url + "#owner")
            page.wait_for_selector(".tile")
            caption("Owner view: coached athletes, logging rate, reply times. Every number comes from the events table.")
            page.wait_for_timeout(4000)
            caption("Cornerwork · coaching between classes · extension tab, Gymdesk side panel, or this link on a phone.")
            page.wait_for_timeout(2500)
            video_path = page.video.path()
            ctx.close()
            browser.close()
    finally:
        server.terminate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)], check=True)
    shutil.rmtree(work, ignore_errors=True)
    print(OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
