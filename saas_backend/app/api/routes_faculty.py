from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_tenant_access
from app.db.database import get_db
from app.models.entities import Faculty, User
from app.schemas.faculty import (
    FacultyCreateRequest,
    FacultyResponse,
    FacultyUpdateRequest,
)

router = APIRouter(prefix="/faculty", tags=["faculty"])


def _get_or_404(faculty_id: int, tenant_id: str, db: Session) -> Faculty:
    row = (
        db.query(Faculty)
        .filter(Faculty.id == faculty_id, Faculty.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Faculty member not found.")
    return row


@router.get("", response_model=list[FacultyResponse])
def list_faculty(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> list[FacultyResponse]:
    rows = db.query(Faculty).filter(Faculty.tenant_id == tenant_id).order_by(Faculty.name).all()
    return [FacultyResponse.model_validate(r) for r in rows]


@router.post("", response_model=FacultyResponse, status_code=201)
def create_faculty(
    payload: FacultyCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> FacultyResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch in payload.")
    row = Faculty(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return FacultyResponse.model_validate(row)


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> FacultyResponse:
    return FacultyResponse.model_validate(_get_or_404(faculty_id, tenant_id, db))


@router.patch("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(
    faculty_id: int,
    payload: FacultyUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> FacultyResponse:
    row = _get_or_404(faculty_id, tenant_id, db)
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return FacultyResponse.model_validate(row)


@router.delete("/{faculty_id}", status_code=204)
def delete_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
    tenant_id: str = Depends(require_tenant_access),
) -> None:
    row = _get_or_404(faculty_id, tenant_id, db)
    db.delete(row)
    db.commit()
