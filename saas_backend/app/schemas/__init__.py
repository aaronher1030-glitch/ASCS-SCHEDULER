"""
Schemas package — exports every public schema class for easy importing.
"""

from app.schemas.auth import TokenResponse, UserCreateRequest
from app.schemas.build_jobs import (
    BuildArtifact,
    BuildConflict,
    BuildJobCreateRequest,
    BuildJobResponse,
    BuildStatus,
    ScheduledClass,
)
from app.schemas.conflict_logs import ConflictLogResponse, ConflictSummary, ResolveConflictLogRequest
from app.schemas.conflicts import ResolveConflictRequest, ConflictResolutionResponse
from app.schemas.faculty import FacultyCreateRequest, FacultyResponse, FacultyUpdateRequest
from app.schemas.imports import ImportValidationResponse
from app.schemas.rooms import RoomCreateRequest, RoomResponse, RoomUpdateRequest
from app.schemas.schedule_entries import (
    BulkCreateRequest,
    BulkFinalizeRequest,
    EntryStatus,
    ScheduleEntryCreateRequest,
    ScheduleEntryResponse,
    ScheduleEntryUpdateRequest,
)
from app.schemas.subjects import SubjectCreateRequest, SubjectResponse, SubjectUpdateRequest

__all__ = [
    # auth
    "TokenResponse",
    "UserCreateRequest",
    # build jobs
    "BuildArtifact",
    "BuildConflict",
    "BuildJobCreateRequest",
    "BuildJobResponse",
    "BuildStatus",
    "ScheduledClass",
    # conflict logs (new)
    "ConflictLogResponse",
    "ConflictSummary",
    "ResolveConflictLogRequest",
    # conflicts (original)
    "ResolveConflictRequest",
    "ConflictResolutionResponse",
    # faculty (new)
    "FacultyCreateRequest",
    "FacultyResponse",
    "FacultyUpdateRequest",
    # imports
    "ImportValidationResponse",
    # rooms (new)
    "RoomCreateRequest",
    "RoomResponse",
    "RoomUpdateRequest",
    # schedule entries (new)
    "BulkCreateRequest",
    "BulkFinalizeRequest",
    "EntryStatus",
    "ScheduleEntryCreateRequest",
    "ScheduleEntryResponse",
    "ScheduleEntryUpdateRequest",
    # subjects (new)
    "SubjectCreateRequest",
    "SubjectResponse",
    "SubjectUpdateRequest",
]
