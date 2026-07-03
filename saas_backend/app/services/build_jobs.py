from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
import time
from uuid import uuid4

from app.db.database import SessionLocal
from app.models.entities import BuildJob, ScheduleVersion
from app.schemas.build_jobs import (
    BuildArtifact,
    BuildConflict,
    BuildJobCreateRequest,
    BuildJobResponse,
    BuildStatus,
    ScheduledClass,
)
from app.services.scheduler_core import assign_rooms, build_and_solve, verify_room_conflicts


class BuildJobService:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._futures: dict[str, Future] = {}
        self._lock = Lock()

    # ──────────────────────────────────────────────────────────
    #  PUBLIC API
    # ──────────────────────────────────────────────────────────

    def create_job(self, payload: BuildJobCreateRequest) -> BuildJobResponse:
        now = datetime.now(timezone.utc)
        job_id = str(uuid4())
        db_job = BuildJob(
            id=job_id,
            tenant_id=payload.tenant_id,
            school_id=payload.school_id,
            status=BuildStatus.queued.value,
            request_payload=payload.model_dump(),
            created_at=now,
            updated_at=now,
            error=None,
            artifact=None,
            progress=5,
        )
        with SessionLocal() as db:
            db.add(db_job)
            db.commit()

        with self._lock:
            self._futures[job_id] = self._executor.submit(self._run_job, job_id, payload)
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> BuildJobResponse | None:
        with SessionLocal() as db:
            db_job = db.query(BuildJob).filter(BuildJob.id == job_id).first()
            if not db_job:
                return None
            return self._to_schema(db_job)

    def get_job_tenant(self, job_id: str) -> str | None:
        with SessionLocal() as db:
            db_job = db.query(BuildJob).filter(BuildJob.id == job_id).first()
            return db_job.tenant_id if db_job else None

    def list_conflicts(self, job_id: str) -> list[BuildConflict]:
        job = self.get_job(job_id)
        if not job or not job.artifact:
            return []
        return job.artifact.conflicts

    def publish(self, job_id: str) -> BuildJobResponse:
        job = self.get_job(job_id)
        if not job:
            raise KeyError("Build job not found.")
        if job.status != BuildStatus.succeeded:
            raise ValueError("Only succeeded jobs can be published.")
        with SessionLocal() as db:
            db_job = db.query(BuildJob).filter(BuildJob.id == job_id).first()
            db_job.status = BuildStatus.published.value
            db_job.progress = 100
            db_job.updated_at = datetime.now(timezone.utc)
            existing_versions = (
                db.query(ScheduleVersion).filter(ScheduleVersion.job_id == job_id).count()
            )
            db.add(ScheduleVersion(
                job_id=job_id,
                tenant_id=db_job.tenant_id,
                school_id=db_job.school_id,
                version_no=existing_versions + 1,
                status="published",
                snapshot=db_job.artifact or {},
            ))
            db.commit()
            db.refresh(db_job)
            return self._to_schema(db_job)

    def wait_for_update(
        self, job_id: str, since_status: str | None, timeout_seconds: int = 20
    ) -> BuildJobResponse | None:
        deadline = time.time() + max(1, timeout_seconds)
        while time.time() < deadline:
            job = self.get_job(job_id)
            if not job:
                return None
            if since_status is None or job.status.value != since_status:
                return job
            time.sleep(0.75)
        return self.get_job(job_id)

    def resolve_conflict(self, job_id: str, conflict_index: int) -> "BuildJobResponse":
        """
        DEPRECATED: Conflict resolution now goes through the ConflictLog table.
        See routes_conflict_logs.py and routes_conflicts.py.
        This method is kept as a stub for backward compat but does nothing.
        """
        raise ValueError(
            "Conflict resolution has been migrated to the ConflictLog system. "
            "Use POST /api/v1/conflict-logs/{log_id}/resolve instead."
        )

    # ──────────────────────────────────────────────────────────
    #  BACKGROUND WORKER
    # ──────────────────────────────────────────────────────────

    def _run_job(self, job_id: str, payload: BuildJobCreateRequest) -> None:
        self._update_job(job_id, status=BuildStatus.running.value, progress=20)
        try:
            sections        = [section.id for section in payload.sections]
            subjects        = [subject.name for subject in payload.subjects]
            lesson_frequency = {subject.name: subject.freq for subject in payload.subjects}
            days            = list(range(payload.days_per_week))
            periods         = list(range(1, payload.periods_per_day + 1))

            # Build teacher assignments dict
            teacher_assignments: dict[str, list[str]] | None = None
            teacher_availability: dict[str, list[bool]] | None = None
            if payload.constraints.prevent_teacher_double_booking and payload.teachers:
                teacher_assignments = {
                    t.name: t.subjects for t in payload.teachers if t.subjects
                }
                # Read availability masks if provided on the teacher payload
                availability_masks = {
                    t.name: getattr(t, "availability", [True] * 40)
                    for t in payload.teachers
                }
                if any(availability_masks.values()):
                    teacher_availability = availability_masks

            self._update_job(job_id, progress=35)

            # ── Call updated solver (returns SolveResult) ────────────────
            result = build_and_solve(
                sections=sections,
                subjects=subjects,
                lesson_frequency=lesson_frequency,
                days=days,
                periods=periods,
                teacher_assignments=teacher_assignments,
                teacher_availability=teacher_availability,
                no_consec_major=payload.constraints.no_consec_major,
                protect_lunch=payload.constraints.protect_lunch,
                seed=42,
            )

            self._update_job(job_id, progress=70)

            # ── Room assignment ──────────────────────────────────────────
            rooms: dict[tuple[int, str], int] = {}
            if payload.constraints.unique_rooms and result.schedule:
                rooms = assign_rooms(result.schedule, max_rooms=payload.max_rooms)

            self._update_job(job_id, progress=85)

            # ── Conflict verification ────────────────────────────────────
            room_conflicts = verify_room_conflicts(result.schedule, rooms)
            conflicts: list[BuildConflict] = [
                BuildConflict(
                    code="ROOM_CONFLICT",
                    message=msg,
                    suggested_action="Run conflict center auto-resolve or manually swap room.",
                )
                for msg in room_conflicts
            ]

            # Flag unassigned subjects from partial solve
            for _sec_id, subject_name, _req in result.unassigned:
                conflicts.append(BuildConflict(
                    code="UNASSIGNED_SUBJECT",
                    message=(
                        f"Subject '{subject_name}' could not be scheduled automatically. "
                        "Use Manual Override to place it."
                    ),
                    suggested_action="Open the Manual Override panel and assign a slot manually.",
                ))

            artifact = BuildArtifact(
                total_classes=len(result.schedule),
                solve_seconds=result.elapsed,
                scheduled_classes=[
                    ScheduledClass(
                        section_id=section_id,
                        subject=subject,
                        day=day,
                        period=period,
                        room=rooms.get((section_id, subject)),
                    )
                    for section_id, subject, day, period in result.schedule
                ],
                conflicts=conflicts,
            )

            # ── Persist conflicts into the unified ConflictLog table ─────
            from app.models.entities import ConflictLog
            with SessionLocal() as log_db:
                for c in conflicts:
                    log_db.add(ConflictLog(
                        conflict_type=c.code,
                        severity="error" if c.code == "ROOM_CONFLICT" else "warning",
                        message=c.message,
                        affected_entries=[],
                        tenant_id=payload.tenant_id,
                    ))
                if conflicts:
                    log_db.commit()

            status = BuildStatus.succeeded.value
            self._update_job(
                job_id,
                status=status,
                artifact=artifact.model_dump(),
                error=None,
                progress=100,
            )

        except Exception as exc:  # pragma: no cover
            self._update_job(
                job_id,
                status=BuildStatus.failed.value,
                error=str(exc),
                progress=100,
            )

    # ──────────────────────────────────────────────────────────
    #  HELPERS
    # ──────────────────────────────────────────────────────────

    def _update_job(self, job_id: str, **kwargs) -> None:
        with SessionLocal() as db:
            db_job = db.query(BuildJob).filter(BuildJob.id == job_id).first()
            if not db_job:
                return
            for key, value in kwargs.items():
                setattr(db_job, key, value)
            db_job.updated_at = datetime.now(timezone.utc)
            db.commit()

    def _to_schema(self, db_job: BuildJob) -> BuildJobResponse:
        return BuildJobResponse(
            job_id=db_job.id,
            status=BuildStatus(db_job.status),
            created_at=db_job.created_at,
            updated_at=db_job.updated_at,
            progress=db_job.progress,
            error=db_job.error,
            artifact=BuildArtifact(**db_job.artifact) if db_job.artifact else None,
        )


build_job_service = BuildJobService()
