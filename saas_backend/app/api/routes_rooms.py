from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_tenant_access
from app.db.database import get_db
from app.models.entities import Room, User
from app.schemas.rooms import (
    RoomCreateRequest,
    RoomResponse,
    RoomUpdateRequest,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


def _get_or_404(room_id: int, tenant_id: str, db: Session) -> Room:
    row = (
        db.query(Room)
        .filter(Room.id == room_id, Room.tenant_id == tenant_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Room not found.")
    return row


@router.get("", response_model=list[RoomResponse])
def list_rooms(
    available_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> list[RoomResponse]:
    q = db.query(Room).filter(Room.tenant_id == tenant_id)
    if available_only:
        q = q.filter(Room.is_available.is_(True))
    rows = q.order_by(Room.floor, Room.room_number).all()
    return [RoomResponse.model_validate(r) for r in rows]


@router.post("", response_model=RoomResponse, status_code=201)
def create_room(
    payload: RoomCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> RoomResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch in payload.")
    # Prevent duplicate room numbers within the same tenant
    existing = (
        db.query(Room)
        .filter(Room.tenant_id == tenant_id, Room.room_number == payload.room_number)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Room '{payload.room_number}' already exists.")
    row = Room(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return RoomResponse.model_validate(row)


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "scheduler", "registrar", "viewer")),
    tenant_id: str = Depends(require_tenant_access),
) -> RoomResponse:
    return RoomResponse.model_validate(_get_or_404(room_id, tenant_id, db))


@router.patch("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    payload: RoomUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "registrar")),
    tenant_id: str = Depends(require_tenant_access),
) -> RoomResponse:
    row = _get_or_404(room_id, tenant_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return RoomResponse.model_validate(row)


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
    tenant_id: str = Depends(require_tenant_access),
) -> None:
    row = _get_or_404(room_id, tenant_id, db)
    db.delete(row)
    db.commit()
