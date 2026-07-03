from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


VALID_YEAR_LEVELS = [
    "Grade 7", "Grade 8", "Grade 9", "Grade 10",
    "Grade 11", "Grade 12",
]

VALID_UNITS = list(range(1, 9))  # 1 – 8 units


class SubjectBase(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=2, max_length=200)
    units: int = Field(default=1, ge=1, le=8)
    year_level: str = Field(default="Grade 7", max_length=20)
    required_hours_per_week: int = Field(default=5, ge=1, le=30)


class SubjectCreateRequest(SubjectBase):
    tenant_id: str = Field(default="default-tenant", max_length=120)


class SubjectUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    title: str | None = Field(default=None, min_length=2, max_length=200)
    units: int | None = Field(default=None, ge=1, le=8)
    year_level: str | None = Field(default=None, max_length=20)
    required_hours_per_week: int | None = Field(default=None, ge=1, le=30)


class SubjectResponse(SubjectBase):
    id: int
    tenant_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
