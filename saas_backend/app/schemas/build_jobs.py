from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BuildStatus(str, Enum):
    queued = "queued"
    running = "running"
    failed = "failed"
    succeeded = "succeeded"
    published = "published"


class SectionInput(BaseModel):
    id: int
    name: str


class SubjectInput(BaseModel):
    name: str
    freq: int = Field(ge=1, le=10)


class TeacherInput(BaseModel):
    name: str
    subjects: list[str] = Field(default_factory=list)


class ConstraintProfileInput(BaseModel):
    no_consec_major: bool = True
    protect_lunch: bool = True
    prevent_teacher_double_booking: bool = True
    unique_rooms: bool = True


class BuildJobCreateRequest(BaseModel):
    tenant_id: str
    school_id: str
    school_name: str
    school_year: str
    terms_per_year: int = Field(default=3, ge=1, le=4)
    program: str = Field(default="SHS")
    days_per_week: int = Field(default=5, ge=3, le=6)
    periods_per_day: int = Field(default=9, ge=1, le=12)
    max_rooms: int = Field(default=35, ge=1, le=500)
    sections: list[SectionInput]
    subjects: list[SubjectInput]
    teachers: list[TeacherInput] = Field(default_factory=list)
    constraints: ConstraintProfileInput = Field(default_factory=ConstraintProfileInput)


class BuildConflict(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    suggested_action: str | None = None


class ScheduledClass(BaseModel):
    section_id: int
    subject: str
    day: int
    period: int
    room: int | None = None


class BuildArtifact(BaseModel):
    total_classes: int
    solve_seconds: float
    scheduled_classes: list[ScheduledClass]
    conflicts: list[BuildConflict] = Field(default_factory=list)


class BuildJobResponse(BaseModel):
    job_id: str
    status: BuildStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    error: str | None = None
    artifact: BuildArtifact | None = None
