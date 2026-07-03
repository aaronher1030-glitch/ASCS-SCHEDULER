from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_tenant_access
from app.db.database import get_db
from app.models.entities import ConflictLog, Faculty, Room, ScheduleEntry, Subject, User
from app.schemas.conflict_logs import (
    ConflictLogResponse,
    ConflictSummary,
    ResolveConflictLogRequest,
)

router = APIRouter(prefix="/conflict-logs", tags=["conflict-logs"])


# ──────────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────────

def _get_or_404(log_id: int, tenant_id: str, db: Session) -> ConflictLog:
    row = (
        db.query(ConflictLog)
        .filter(ConflictLog.id == log_id, ConflictLog.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Conflict log entry not found.")
    return row


def _run_validation(tenant_id: str, db: Session) -> list[ConflictLog]:
    """
    Background validation service.
    Scans all ScheduleEntry rows for the tenant and produces ConflictLog records
    for every detected logical error. Previous auto-generated logs are purged first
    so the list always reflects the current state of the schedule.
    """
    # Clear previous auto-generated (unresolved) logs
    db.query(ConflictLog).filter(
        ConflictLog.tenant_id == tenant_id,
        ConflictLog.is_resolved.is_(False),
    ).delete(synchronize_session=False)

    entries = (
        db.query(ScheduleEntry)
        .filter(ScheduleEntry.tenant_id == tenant_id)
        .all()
    )
    new_logs: list[ConflictLog] = []

    # ── 1. Room double-booking ──────────────────────────────
    room_slot_map: dict[tuple[int | None, int, int], list[int]] = {}
    for entry in entries:
        if entry.room_id is None:
            continue
        key = (entry.room_id, entry.day_of_week, entry.time_slot)
        room_slot_map.setdefault(key, []).append(entry.id)

    for (room_id, day, slot), ids in room_slot_map.items():
        if len(ids) > 1:
            room = db.query(Room).filter(Room.id == room_id).first()
            rnum = room.room_number if room else str(room_id)
            log = ConflictLog(
                conflict_type="ROOM_DOUBLE_BOOK",
                severity="error",
                message=(
                    f"Room '{rnum}' is double-booked on day={day} slot={slot} "
                    f"by entries {ids}."
                ),
                affected_entries=ids,
                tenant_id=tenant_id,
            )
            db.add(log)
            new_logs.append(log)

    # ── 2. Faculty double-booking ───────────────────────────
    faculty_slot_map: dict[tuple[int | None, int, int], list[int]] = {}
    for entry in entries:
        if entry.faculty_id is None:
            continue
        key = (entry.faculty_id, entry.day_of_week, entry.time_slot)
        faculty_slot_map.setdefault(key, []).append(entry.id)

    for (faculty_id, day, slot), ids in faculty_slot_map.items():
        if len(ids) > 1:
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
            fname = faculty.name if faculty else str(faculty_id)
            log = ConflictLog(
                conflict_type="FACULTY_DOUBLE_BOOK",
                severity="error",
                message=(
                    f"Faculty '{fname}' is double-booked on day={day} slot={slot} "
                    f"by entries {ids}."
                ),
                affected_entries=ids,
                tenant_id=tenant_id,
            )
            db.add(log)
            new_logs.append(log)

    # ── 3. Faculty availability violation ──────────────────
    for entry in entries:
        if entry.faculty_id is None:
            continue
        faculty = db.query(Faculty).filter(Faculty.id == entry.faculty_id).first()
        if not faculty:
            continue
        mask: list[bool] = faculty.binary_availability_mask or [True] * 40
        mask_index = entry.day_of_week * 8 + (entry.time_slot - 1)
        if mask_index < len(mask) and not mask[mask_index]:
            log = ConflictLog(
                conflict_type="AVAILABILITY_VIOLATION",
                severity="error",
                message=(
                    f"Faculty '{faculty.name}' is marked unavailable at "
                    f"day={entry.day_of_week} slot={entry.time_slot} "
                    f"(entry id={entry.id})."
                ),
                affected_entries=[entry.id],
                tenant_id=tenant_id,
            )
            db.add(log)
            new_logs.append(log)

    # ── 4. Room capacity warnings ───────────────────────────
    for entry in entries:
        if entry.room_id is None:
            continue
        room = db.query(Room).filter(Room.id == entry.room_id).first()
        if room and room.capacity < 20:
            log = ConflictLog(
                conflict_type="ROOM_CAPACITY",
                severity="warning",
                message=(
                    f"Room '{room.room_number}' (capacity={room.capacity}) "
                    f"is very small for entry id={entry.id} section='{entry.section_name}'."
                ),
                affected_entries=[entry.id],
                tenant_id=tenant_id,
            )
            db.add(log)
            new_logs.append(log)

    # ── 5. Missing room assignment ──────────────────────────
    for entry in entries:
        if entry.room_id is None and entry.status == "finalized":
            log = ConflictLog(
                conflict_type="MISSING_ROOM",
                severity="warning",
                message=(
                    f"Finalized entry id={entry.id} for section='{entry.section_name}' "
                    f"has no room assigned."
                ),
                affected_entries=[entry.id],
                tenant_id=tenant_id,
            )
            db.add(log)
            new_logs.append(log)

    # ── 6. Subject hours not met ────────────────────────────
    subject_entry_counts: dict[int, int] = {}
    for entry in entries:
        subject_entry_counts[entry.subject_id] = subject_entry_counts.get(entry.subject_id, 0) + 1

    for subj_id, count in subject_entry_counts.items():
        subj = db.query(Subject).filter(Subject.id == subj_id, Subject.tenant_id == tenant_id).first()
        if subj and count < subj.required_hours_per_week:
            log = ConflictLog(
                conflict_type="HOURS_DEFICIT",
                severity="warning",
                message=(
                    f"Subject '{subj.title}' ({subj.code}) has only {count} "
                    f"of {subj.required_hours_per_week} required periods scheduled."
                ),
                affected_entries=[],
                tenant_id=tenant_id,
            )
            db.add(log)
            new_logs.append(log)

    db.commit()
    return new_logs


# ──────────────────────────────────────────────────────────────
#  ENDPOINTS
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[ConflictLogResponse])
def list_conflict_logs(
    severity: str | None = None,
    resolved: bool | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> list[ConflictLogResponse]:
    q = db.query(ConflictLog).filter(ConflictLog.tenant_id == tenant_id)
    if severity:
        q = q.filter(ConflictLog.severity == severity)
    if resolved is not None:
        q = q.filter(ConflictLog.is_resolved.is_(resolved))
    rows = q.order_by(ConflictLog.created_at.desc()).all()
    return [ConflictLogResponse.model_validate(r) for r in rows]


@router.post("/validate", response_model=dict[str, int])
def run_validation(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> dict[str, int]:
    """Trigger the background validation service manually. Returns count of new conflicts found."""
    new_logs = _run_validation(tenant_id, db)
    return {"conflicts_found": len(new_logs)}


@router.get("/summary", response_model=ConflictSummary)
def get_conflict_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> ConflictSummary:
    """Aggregated counts for the metrics dashboard."""
    rows = db.query(ConflictLog).filter(ConflictLog.tenant_id == tenant_id).all()
    return ConflictSummary(
        total=len(rows),
        errors=sum(1 for r in rows if r.severity == "error"),
        warnings=sum(1 for r in rows if r.severity == "warning"),
        resolved=sum(1 for r in rows if r.is_resolved),
        unresolved=sum(1 for r in rows if not r.is_resolved),
    )


@router.post("/{log_id}/resolve", response_model=ConflictLogResponse)
def resolve_conflict_log(
    log_id: int,
    payload: ResolveConflictLogRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> ConflictLogResponse:
    row = _get_or_404(log_id, tenant_id, db)
    if row.is_resolved:
        raise HTTPException(status_code=400, detail="Conflict already resolved.")
    row.is_resolved = True
    row.resolved_by = payload.resolved_by
    row.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return ConflictLogResponse.model_validate(row)
