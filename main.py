import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db.database import init_db
from routers import repos, scans, ws
from services.ws_manager import manager

settings = get_settings()

app = FastAPI(
    title="Doc-Drift Guardian",
    description="Multi-agent system (built on Google ADK) that detects documentation "
                 "drift after code changes and drafts the fix.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router)
app.include_router(scans.router)
app.include_router(ws.router)


@app.on_event("startup")
async def on_startup():
    init_db()
    manager.set_loop(asyncio.get_running_loop())


@app.get("/api/health")
def health():
    return {"status": "ok", "model": settings.adk_model}
