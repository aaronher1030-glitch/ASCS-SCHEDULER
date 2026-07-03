from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_build_jobs import router as build_jobs_router
from app.api.routes_conflict_logs import router as conflict_logs_router
from app.api.routes_conflicts import router as conflicts_router
from app.api.routes_faculty import router as faculty_router
from app.api.routes_imports import router as imports_router
from app.api.routes_rooms import router as rooms_router
from app.api.routes_schedule_entries import router as schedule_entries_router
from app.api.routes_subjects import router as subjects_router
from app.db.database import Base, engine
from app.models import entities  # noqa: F401  — registers all ORM models with Base


# ── Create all tables that are not yet in the DB (safe for SQLite dev) ──────
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SCAS Scheduler API",
    version="0.2.0",
    description=(
        "Multi-tenant AI-powered Automated Scheduling System — "
        "FastAPI + SQLAlchemy + OR-Tools CP-SAT."
    ),
)

import os

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:6767,http://localhost:3000,http://localhost:8501"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Original routers ─────────────────────────────────────────────────────────
app.include_router(auth_router,         prefix="/api/v1", tags=["auth"])
app.include_router(build_jobs_router,   prefix="/api/v1", tags=["build-jobs"])
app.include_router(conflicts_router,    prefix="/api/v1", tags=["conflicts"])
app.include_router(imports_router,      prefix="/api/v1", tags=["imports"])

# ── Phase-1/2 domain routers ─────────────────────────────────────────────────
app.include_router(faculty_router,          prefix="/api/v1", tags=["faculty"])
app.include_router(rooms_router,            prefix="/api/v1", tags=["rooms"])
app.include_router(subjects_router,         prefix="/api/v1", tags=["subjects"])
app.include_router(schedule_entries_router, prefix="/api/v1", tags=["schedule-entries"])
app.include_router(conflict_logs_router,    prefix="/api/v1", tags=["conflict-logs"])


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0"}

from app.api.routes_ai import router as ai_router
app.include_router(ai_router, prefix="/api/v1", tags=["ai"])
