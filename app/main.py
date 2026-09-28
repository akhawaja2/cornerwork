"""Cornerwork backend: JSON API for the extension/PWA. No HTML except /c/{token} (Phase 1.6)."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.slices.brief.router import router as brief
from app.slices.logs.router import router as logs
from app.slices.owner.router import router as owner
from app.slices.replies.router import router as replies
from app.slices.roster.router import router as roster


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="Cornerwork backend", lifespan=lifespan, docs_url=None, redoc_url=None)
for r in (logs, replies, brief, roster, owner):
    app.include_router(r)


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8765")))
