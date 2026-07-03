from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_tenant_access
from app.db.database import get_db
from app.models.entities import Room, ScheduleEntry, Subject, User
from app.schemas.schedule_entries import (
    BulkCreateRequest,
    BulkFinalizeRequest,
    EntryStatus,
    ScheduleEntryCreateRequest,
    ScheduleEntryResponse,
    ScheduleEntryUpdateRequest,
)

router = APIRouter(prefix="/schedule-entries", tags=["schedule-entries"])


def _get_or_404(entry_id: int, tenant_id: str, db: Session) -> ScheduleEntry:
    row = (
        db.query(ScheduleEntry)
        .filter(ScheduleEntry.id == entry_id, ScheduleEntry.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Schedule entry not found.")
    return row


def _check_overlap(
    db: Session,
    tenant_id: str,
    section_name: str,
    day_of_week: int,
    time_slot: int,
    exclude_id: int | None = None,
) -> None:
    """Raise 409 if the same section already has an entry at (day, slot)."""
    q = (
        db.query(ScheduleEntry)
        .filter(
            ScheduleEntry.tenant_id == tenant_id,
            ScheduleEntry.section_name == section_name,
            ScheduleEntry.day_of_week == day_of_week,
            ScheduleEntry.time_slot == time_slot,
        )
    )
    if exclude_id is not None:
        q = q.filter(ScheduleEntry.id != exclude_id)
    if q.first():
        raise HTTPException(
            status_code=409,
            detail=(
                f"Section '{section_name}' already has an entry at "
                f"day={day_of_week} slot={time_slot}."
            ),
        )


def _check_room_overlap(
    db: Session,
    tenant_id: str,
    room_id: int,
    day_of_week: int,
    time_slot: int,
    exclude_id: int | None = None,
) -> None:
    """Raise 409 if the same room is already booked at (day, slot)."""
    q = (
        db.query(ScheduleEntry)
        .filter(
            ScheduleEntry.tenant_id == tenant_id,
            ScheduleEntry.room_id == room_id,
            ScheduleEntry.day_of_week == day_of_week,
            ScheduleEntry.time_slot == time_slot,
        )
    )
    if exclude_id is not None:
        q = q.filter(ScheduleEntry.id != exclude_id)
    if q.first():
        raise HTTPException(
            status_code=409,
            detail=f"Room id={room_id} is already booked at day={day_of_week} slot={time_slot}.",
        )


# ──────────────────────────────────────────────────────────────
#  CRUD
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[ScheduleEntryResponse])
def list_entries(
    section_name: str | None = None,
    status: str | None = None,
    job_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> list[ScheduleEntryResponse]:
    q = db.query(ScheduleEntry).filter(ScheduleEntry.tenant_id == tenant_id)
    if section_name:
        q = q.filter(ScheduleEntry.section_name == section_name)
    if status:
        q = q.filter(ScheduleEntry.status == status)
    if job_id:
        q = q.filter(ScheduleEntry.job_id == job_id)
    rows = q.order_by(ScheduleEntry.section_name, ScheduleEntry.day_of_week, ScheduleEntry.time_slot).all()
    return [ScheduleEntryResponse.model_validate(r) for r in rows]


@router.post("", response_model=ScheduleEntryResponse, status_code=201)
def create_entry(
    payload: ScheduleEntryCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> ScheduleEntryResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch in payload.")
    # Verify subject exists in tenant
    if not db.query(Subject).filter(Subject.id == payload.subject_id, Subject.tenant_id == tenant_id).first():
        raise HTTPException(status_code=404, detail="Subject not found in this tenant.")
    _check_overlap(db, tenant_id, payload.section_name, payload.day_of_week, payload.time_slot)
    if payload.room_id:
        _check_room_overlap(db, tenant_id, payload.room_id, payload.day_of_week, payload.time_slot)
    row = ScheduleEntry(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return ScheduleEntryResponse.model_validate(row)


@router.post("/bulk", response_model=dict[str, int], status_code=201)
def bulk_create_entries(
    payload: BulkCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> dict[str, int]:
    """Bulk-insert solver output entries (skips duplicates silently)."""
    inserted = 0
    for entry in payload.entries:
        if entry.tenant_id != tenant_id:
            continue
        exists = (
            db.query(ScheduleEntry)
            .filter(
                ScheduleEntry.tenant_id == tenant_id,
                ScheduleEntry.section_name == entry.section_name,
                ScheduleEntry.day_of_week == entry.day_of_week,
                ScheduleEntry.time_slot == entry.time_slot,
            )
            .first()
        )
        if exists:
            continue
        row = ScheduleEntry(**entry.model_dump())
        db.add(row)
        inserted += 1
    db.commit()
    return {"inserted": inserted}


@router.get("/{entry_id}", response_model=ScheduleEntryResponse)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> ScheduleEntryResponse:
    return ScheduleEntryResponse.model_validate(_get_or_404(entry_id, tenant_id, db))


@router.patch("/{entry_id}", response_model=ScheduleEntryResponse)
def update_entry(
    entry_id: int,
    payload: ScheduleEntryUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> ScheduleEntryResponse:
    """Manual override: reassign faculty, room, day, or slot."""
    row = _get_or_404(entry_id, tenant_id, db)
    update_data = payload.model_dump(exclude_none=True)
    # Overlap checks before committing
    new_day = update_data.get("day_of_week", row.day_of_week)
    new_slot = update_data.get("time_slot", row.time_slot)
    _check_overlap(db, tenant_id, row.section_name, new_day, new_slot, exclude_id=entry_id)
    new_room = update_data.get("room_id", row.room_id)
    if new_room:
        _check_room_overlap(db, tenant_id, new_room, new_day, new_slot, exclude_id=entry_id)
    # Validate room capacity vs subject year level (soft check — just warn via HTTP header)
    headers: dict[str, str] = {}
    if new_room:
        room = db.query(Room).filter(Room.id == new_room).first()
        if room and room.capacity < 30:
            headers["X-Capacity-Warning"] = f"Room {room.room_number} capacity={room.capacity} may be too small."
    for field, value in update_data.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    from fastapi.responses import JSONResponse
    return ScheduleEntryResponse.model_validate(row)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> None:
    row = _get_or_404(entry_id, tenant_id, db)
    db.delete(row)
    db.commit()


# ──────────────────────────────────────────────────────────────
#  BULK FINALIZE / RESET
# ──────────────────────────────────────────────────────────────

@router.post("/finalize", response_model=dict[str, int])
def bulk_finalize(
    payload: BulkFinalizeRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> dict[str, int]:
    """
    Finalize all pending entries for a job (commit to production),
    or reset them back to pending if action='reset'.
    """
    new_status = EntryStatus.finalized if payload.action == "finalize" else EntryStatus.pending
    rows = (
        db.query(ScheduleEntry)
        .filter(ScheduleEntry.tenant_id == tenant_id, ScheduleEntry.job_id == payload.job_id)
        .all()
    )
    for row in rows:
        row.status = new_status.value
    db.commit()
    return {"updated": len(rows)}


@router.delete("/job/{job_id}", status_code=200)
def delete_job_entries(
    job_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler")),
    tenant_id: str = Depends(require_tenant_access),
) -> dict[str, int]:
    """Delete all schedule entries for a given job (undo / discard AI result)."""
    rows = (
        db.query(ScheduleEntry)
        .filter(ScheduleEntry.tenant_id == tenant_id, ScheduleEntry.job_id == job_id)
        .all()
    )
    count = len(rows)
    for row in rows:
        db.delete(row)
    db.commit()
    return {"deleted": count}
