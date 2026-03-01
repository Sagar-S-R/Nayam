"""
NAYAM (नयम्) — Sync Pydantic Schemas (Phase 4).

Request / response models for the sync-queue and conflict APIs.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.sync.models import SyncOperation, SyncStatus
from app.sync.conflict_model import ConflictResolution


# ── Sync Queue ───────────────────────────────────────────────────────

class SyncEnqueueRequest(BaseModel):
    """Request body to add an entry to the sync queue."""
    node_id: str = Field(..., min_length=1, max_length=100)
    operation: SyncOperation
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: UUID
    payload: Optional[Dict[str, Any]] = None
    priority: int = Field(default=5, ge=1, le=10)


class SyncEntryResponse(BaseModel):
    """Single sync-queue entry in responses."""
    id: UUID
    node_id: str
    operation: SyncOperation
    resource_type: str
    resource_id: UUID
    payload: Optional[Dict[str, Any]]
    version: int
    status: SyncStatus
    priority: int
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    checksum: Optional[str]
    created_at: datetime
    synced_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SyncListResponse(BaseModel):
    """Paginated list of sync-queue entries."""
    total: int
    entries: List[SyncEntryResponse]


class SyncStatusSummaryResponse(BaseModel):
    """Counts by sync status."""
    summary: Dict[str, int]


# ── Conflict ─────────────────────────────────────────────────────────

class ConflictResolveRequest(BaseModel):
    """Request body to resolve a sync conflict."""
    resolution: ConflictResolution
    resolved_by: Optional[UUID] = None
    notes: Optional[str] = Field(None, max_length=2000)


class ConflictResponse(BaseModel):
    """Single conflict-log entry in responses."""
    id: UUID
    sync_queue_id: Optional[UUID]
    node_id: str
    resource_type: str
    resource_id: UUID
    local_data: Optional[Dict[str, Any]]
    server_data: Optional[Dict[str, Any]]
    resolution: ConflictResolution
    resolved_by: Optional[UUID]
    resolution_notes: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ConflictListResponse(BaseModel):
    """Paginated conflict list."""
    total: int
    conflicts: List[ConflictResponse]
