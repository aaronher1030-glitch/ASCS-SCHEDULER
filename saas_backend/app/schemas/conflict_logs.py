from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConflictLogResponse(BaseModel):
    id: int
    conflict_type: str
    severity: str
    message: str
    affected_entries: list[int]
    is_resolved: bool
    resolved_by: str | None
    resolved_at: datetime | None
    tenant_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResolveConflictLogRequest(BaseModel):
    resolved_by: str = Field(min_length=1, max_length=100)


class ConflictSummary(BaseModel):
    """Aggregated counts returned by the metrics dashboard endpoint."""
    total: int
    errors: int
    warnings: int
    resolved: int
    unresolved: int
