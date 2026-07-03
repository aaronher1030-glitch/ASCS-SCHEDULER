from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RoomBase(BaseModel):
    room_number: str = Field(min_length=1, max_length=50)
    capacity: int = Field(default=40, ge=1, le=2000)
    floor: int = Field(default=1, ge=0, le=50)
    is_available: bool = Field(default=True)


class RoomCreateRequest(RoomBase):
    tenant_id: str = Field(default="default-tenant", max_length=120)


class RoomUpdateRequest(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=50)
    capacity: int | None = Field(default=None, ge=1, le=2000)
    floor: int | None = Field(default=None, ge=0, le=50)
    is_available: bool | None = None


class RoomResponse(RoomBase):
    id: int
    tenant_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
