from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FacultyBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    department: str = Field(default="General", max_length=100)
    employment_type: str = Field(default="Full-time", pattern="^(Full-time|Part-time)$")
    # 40-element boolean list: 5 days × 8 periods, True = available
    binary_availability_mask: list[bool] = Field(
        default_factory=lambda: [True] * 40,
        min_length=40,
        max_length=40,
    )


class FacultyCreateRequest(FacultyBase):
    tenant_id: str = Field(default="default-tenant", max_length=120)


class FacultyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    department: str | None = Field(default=None, max_length=100)
    employment_type: str | None = Field(default=None, pattern="^(Full-time|Part-time)$")
    binary_availability_mask: list[bool] | None = Field(
        default=None, min_length=40, max_length=40
    )


class FacultyResponse(FacultyBase):
    id: int
    tenant_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
