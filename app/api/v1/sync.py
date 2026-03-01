"""
NAYAM (नयम्) — Sync API Routes (Phase 4).

Endpoints for sync-queue management, lifecycle transitions,
conflict detection and resolution.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.sync import (
    SyncEnqueueRequest,
    SyncEntryResponse,
    SyncListResponse,
    SyncStatusSummaryResponse,
    ConflictResolveRequest,
    ConflictResponse,
    ConflictListResponse,
)
from app.schemas.user import MessageResponse
from app.sync.service import SyncService

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Queue Management ─────────────────────────────────────────────────

@router.post(
    "/queue",
    response_model=SyncEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enqueue a sync entry",
)
def enqueue_sync(
    payload: SyncEnqueueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncEntryResponse:
    """Add an offline operation to the sync queue."""
    svc = SyncService(db)
    entry = svc.enqueue(
        node_id=payload.node_id,
        operation=payload.operation,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        payload=payload.payload,
        priority=payload.priority,
    )
    return SyncEntryResponse.model_validate(entry)


@router.get(
    "/queue",
    response_model=SyncListResponse,
    summary="List pending sync entries",
)
def list_pending(
    node_id: Optional[str] = Query(None, description="Filter by edge node"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncListResponse:
    """List pending sync-queue entries with optional node filter."""
    svc = SyncService(db)
    items, total = svc.list_pending(node_id=node_id, skip=skip, limit=limit)
    return SyncListResponse(
        total=total,
        entries=[SyncEntryResponse.model_validate(i) for i in items],
    )


@router.get(
    "/queue/status",
    response_model=SyncStatusSummaryResponse,
    summary="Sync status summary",
)
def sync_status_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncStatusSummaryResponse:
    """Return counts grouped by sync status."""
    svc = SyncService(db)
    return SyncStatusSummaryResponse(summary=svc.status_summary())


@router.get(
    "/queue/{sync_id}",
    response_model=SyncEntryResponse,
    summary="Get sync entry details",
)
def get_sync_entry(
    sync_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncEntryResponse:
    """Retrieve a single sync-queue entry by ID."""
    svc = SyncService(db)
    entry = svc.get_entry(sync_id)
    return SyncEntryResponse.model_validate(entry)


# ── Lifecycle Transitions ────────────────────────────────────────────

@router.post(
    "/queue/{sync_id}/begin",
    response_model=SyncEntryResponse,
    summary="Begin sync (PENDING → IN_PROGRESS)",
)
def begin_sync(
    sync_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncEntryResponse:
    """Transition a sync entry from PENDING to IN_PROGRESS."""
    svc = SyncService(db)
    return SyncEntryResponse.model_validate(svc.begin_sync(sync_id))


@router.post(
    "/queue/{sync_id}/complete",
    response_model=SyncEntryResponse,
    summary="Complete sync (IN_PROGRESS → SYNCED)",
)
def complete_sync(
    sync_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncEntryResponse:
    """Transition a sync entry from IN_PROGRESS to SYNCED."""
    svc = SyncService(db)
    return SyncEntryResponse.model_validate(svc.complete_sync(sync_id))


@router.post(
    "/queue/{sync_id}/fail",
    response_model=SyncEntryResponse,
    summary="Fail sync (IN_PROGRESS → FAILED)",
)
def fail_sync(
    sync_id: UUID,
    error: str = Query(..., description="Error message"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncEntryResponse:
    """Mark a sync entry as failed."""
    svc = SyncService(db)
    return SyncEntryResponse.model_validate(svc.fail_sync(sync_id, error))


@router.post(
    "/queue/retry",
    response_model=SyncListResponse,
    summary="Retry failed entries",
)
def retry_failed(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> SyncListResponse:
    """Reset retryable failed entries back to PENDING."""
    svc = SyncService(db)
    reset = svc.retry_failed()
    return SyncListResponse(
        total=len(reset),
        entries=[SyncEntryResponse.model_validate(r) for r in reset],
    )


@router.get(
    "/queue/{sync_id}/verify",
    summary="Verify entry checksum",
)
def verify_checksum(
    sync_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Verify the SHA-256 checksum of a sync-queue entry's payload."""
    svc = SyncService(db)
    valid = svc.verify_checksum(sync_id)
    return {"sync_id": str(sync_id), "checksum_valid": valid}


# ── Conflict Resolution ──────────────────────────────────────────────

@router.get(
    "/conflicts",
    response_model=ConflictListResponse,
    summary="List pending conflicts",
)
def list_conflicts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConflictListResponse:
    """List unresolved sync conflicts."""
    svc = SyncService(db)
    items, total = svc.list_pending_conflicts(skip=skip, limit=limit)
    return ConflictListResponse(
        total=total,
        conflicts=[ConflictResponse.model_validate(c) for c in items],
    )


@router.post(
    "/conflicts/{conflict_id}/resolve",
    response_model=ConflictResponse,
    summary="Resolve a conflict",
)
def resolve_conflict(
    conflict_id: UUID,
    payload: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> ConflictResponse:
    """Resolve a pending sync conflict."""
    svc = SyncService(db)
    resolved = svc.resolve_conflict(
        conflict_id=conflict_id,
        resolution=payload.resolution,
        resolved_by=payload.resolved_by or current_user.id,
        notes=payload.notes,
    )
    return ConflictResponse.model_validate(resolved)
