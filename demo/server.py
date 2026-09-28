"""Loopback-only offline demo. No credentials, cloud calls or real messaging."""
from pathlib import Path
from contextlib import contextmanager
from typing import Literal
import os
import sqlite3
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

try:
    from . import core
except ImportError:
    import core

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('CORNERWORK_DB', str(ROOT / 'data' / 'demo.sqlite3')))
LOCK = threading.RLock()
app = FastAPI(title='Cornerwork offline demo', docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])

@contextmanager
def database():
    with LOCK:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = core.init_db(str(DB_PATH))
        try:
            core.seed(conn)
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

@app.middleware('http')
async def local_only(request: Request, call_next):
    if request.method == 'POST':
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': 'Cross-origin writes are disabled.'}, status_code=403)
        if int(request.headers.get('content-length', 0)) > 1_000_000:
            return JSONResponse({'detail': 'Request too large.'}, status_code=413)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
    return response

@app.exception_handler(ValueError)
async def invalid_input(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=400)

@app.exception_handler(sqlite3.IntegrityError)
async def invalid_record(request, exc):
    return JSONResponse({'detail': 'This record conflicts with existing demo data.'}, status_code=400)

@app.get('/')
def home():
    return FileResponse(ROOT / 'static' / 'index.html')

@app.get('/health')
def health():
    with database() as conn:
        conn.execute('SELECT 1')
    return {'ok': True, 'mode': 'offline-demo', 'external_services': False}

@app.get('/api/state')
def state(role: Literal['coach','owner'] = 'coach'):
    with database() as conn:
        return core.state(conn, role=role)

class Inbound(BaseModel):
    phone: str = Field(min_length=1, max_length=30)
    body: str = Field(min_length=1, max_length=5000)
    kind: Literal['text','voice'] = 'text'
    request_id: str | None = Field(default=None, max_length=100)

@app.post('/api/inbound')
def inbound(payload: Inbound):
    with database() as conn:
        return core.inbound(conn, **payload.model_dump())

class Reply(BaseModel):
    log_id: int = Field(gt=0)
    body: str = Field(min_length=1, max_length=2000)
    request_id: str | None = Field(default=None, max_length=100)

@app.post('/api/reply')
def reply(payload: Reply):
    with database() as conn:
        return core.reply(conn, **payload.model_dump())

@app.get('/api/brief')
def brief(class_id: int = 1, date: str | None = None):
    with database() as conn:
        if date is None:
            current = core.state(conn, role='coach')
            date = current['brief']['date']
        return core.brief(conn, class_id, date)

class Jobs(BaseModel):
    now: str | None = None

@app.post('/api/jobs')
def jobs(payload: Jobs):
    with database() as conn:
        return core.jobs(conn, payload.now)

class ImportCSV(BaseModel):
    kind: Literal['athletes','bookings']
    csv: str = Field(min_length=1, max_length=500000)

@app.post('/api/import')
def import_csv(payload: ImportCSV):
    with database() as conn:
        return core.import_csv(conn, payload.kind, payload.csv)

@app.post('/api/reset')
def reset():
    # The fixed, app-owned demo database only. No user-supplied delete paths.
    with LOCK:
        with database() as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            conn.execute('PRAGMA foreign_keys=OFF')
            for row in tables:
                name = row[0].replace('"', '""')
                conn.execute(f'DROP TABLE "{name}"')
            conn.commit()
        with database() as conn:
            pass
    return {'ok': True, 'message': 'Fictional demo data restored.'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('PORT','8765')))
