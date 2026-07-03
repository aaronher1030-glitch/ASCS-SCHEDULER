from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_tenant_access
from app.db.database import get_db
from app.models.entities import Subject, User
from app.schemas.subjects import (
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
    VALID_YEAR_LEVELS,
)

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _get_or_404(subject_id: int, tenant_id: str, db: Session) -> Subject:
    row = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Subject not found.")
    return row


def _validate_year_level(year_level: str | None) -> None:
    if year_level and year_level not in VALID_YEAR_LEVELS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid year_level '{year_level}'. Must be one of: {VALID_YEAR_LEVELS}",
        )


@router.get("", response_model=list[SubjectResponse])
def list_subjects(
    year_level: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> list[SubjectResponse]:
    q = db.query(Subject).filter(Subject.tenant_id == tenant_id)
    if year_level:
        q = q.filter(Subject.year_level == year_level)
    rows = q.order_by(Subject.year_level, Subject.code).all()
    return [SubjectResponse.model_validate(r) for r in rows]


@router.post("", response_model=SubjectResponse, status_code=201)
def create_subject(
    payload: SubjectCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> SubjectResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch in payload.")
    _validate_year_level(payload.year_level)
    # Validate units vs required_hours_per_week
    if payload.required_hours_per_week < payload.units:
        raise HTTPException(
            status_code=422,
            detail=(
                f"required_hours_per_week ({payload.required_hours_per_week}) cannot be "
                f"less than units ({payload.units})."
            ),
        )
    # Prevent duplicate subject codes within the same tenant
    existing = (
        db.query(Subject)
        .filter(Subject.tenant_id == tenant_id, Subject.code == payload.code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Subject code '{payload.code}' already exists.")
    row = Subject(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return SubjectResponse.model_validate(row)


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> SubjectResponse:
    return SubjectResponse.model_validate(_get_or_404(subject_id, tenant_id, db))


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    payload: SubjectUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> SubjectResponse:
    row = _get_or_404(subject_id, tenant_id, db)
    _validate_year_level(payload.year_level)
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(row, field, value)
    # Re-validate units vs hours after patch
    if row.required_hours_per_week < row.units:
        raise HTTPException(
            status_code=422,
            detail=(
                f"required_hours_per_week ({row.required_hours_per_week}) cannot be "
                f"less than units ({row.units})."
            ),
        )
    db.commit()
    db.refresh(row)
    return SubjectResponse.model_validate(row)


@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
    tenant_id: str = Depends(require_tenant_access),
) -> None:
    row = _get_or_404(subject_id, tenant_id, db)
    db.delete(row)
    db.commit()
