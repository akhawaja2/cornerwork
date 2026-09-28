"""Cornerwork backend: JSON API for the extension/PWA plus one HTML route, /c/{token}, that serves
the same dashboard bundle for phones (web adapter)."""
import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.db import get_session, init_db
from app.deps import gym_for_token
from app.slices.brief.router import router as brief
from app.slices.inbound.router import router as inbound
from app.slices.logs.router import router as logs
from app.slices.owner.router import router as owner
from app.slices.replies.router import router as replies
from app.slices.roster.router import router as roster

mimetypes.add_type("application/javascript", ".js")  # Windows registry often maps .js to text/plain, which breaks module scripts
EXT = Path(__file__).resolve().parents[1] / "extension-demo"
PLACEHOLDER = "<!doctype html><html><head><title>Cornerwork</title></head><body><p>Dashboard bundle arrives in Phase 2.</p></body></html>"


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="Cornerwork backend", lifespan=lifespan, docs_url=None, redoc_url=None)
for r in (logs, replies, brief, roster, owner, inbound):
    app.include_router(r)
app.mount("/static", StaticFiles(directory=EXT), name="static")  # ponytail: whole extension folder; trim to a bundle dir if it grows


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/c/{token}", response_class=HTMLResponse)
def web_dashboard(token: str, session: Session = Depends(get_session)):
    """Magic link: the extension's dashboard.html with the web adapter selected. Token stays in the URL only."""
    if not gym_for_token(session, token):
        raise HTTPException(404)
    page = EXT / "dashboard.html"
    html = page.read_text(encoding="utf-8") if page.exists() else PLACEHOLDER
    html = html.replace("<head>", '<head><base href="/static/"><script>window.CW_ADAPTER="web"</script>', 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8765")))
