"""
NAYAM (नयम्) — Offline API Routes (Phase 4).

Endpoints for offline action caching, listing, and queue promotion.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.offline import (
    OfflineCacheRequest,
    OfflineActionResponse,
    OfflineListResponse,
    OfflineStatusSummaryResponse,
    OfflinePromoteAllResponse,
)
from app.offline.service import OfflineService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/actions",
    response_model=OfflineActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cache an offline action",
)
def cache_action(
    payload: OfflineCacheRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OfflineActionResponse:
    """Store a user action in the offline cache."""
    svc = OfflineService(db)
    action = svc.cache_action(
        node_id=payload.node_id,
        user_id=payload.user_id or current_user.id,
        action_type=payload.action_type,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        payload=payload.payload,
    )
    return OfflineActionResponse.model_validate(action)


@router.get(
    "/actions",
    response_model=OfflineListResponse,
    summary="List cached offline actions",
)
def list_cached(
    node_id: Optional[str] = Query(None, description="Filter by node"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OfflineListResponse:
    """List offline actions currently in CACHED state."""
    svc = OfflineService(db)
    items, total = svc.list_cached(node_id=node_id, skip=skip, limit=limit)
    return OfflineListResponse(
        total=total,
        actions=[OfflineActionResponse.model_validate(a) for a in items],
    )


@router.get(
    "/actions/status",
    response_model=OfflineStatusSummaryResponse,
    summary="Offline status summary",
)
def offline_status_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OfflineStatusSummaryResponse:
    """Return counts grouped by offline action status."""
    svc = OfflineService(db)
    return OfflineStatusSummaryResponse(summary=svc.status_summary())


@router.get(
    "/actions/{action_id}",
    response_model=OfflineActionResponse,
    summary="Get offline action details",
)
def get_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OfflineActionResponse:
    """Retrieve a single offline action by ID."""
    svc = OfflineService(db)
    return OfflineActionResponse.model_validate(svc.get_action(action_id))


@router.post(
    "/actions/{action_id}/promote",
    response_model=OfflineActionResponse,
    summary="Promote action to sync queue",
)
def promote_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OfflineActionResponse:
    """Move a CACHED action to the sync queue (CACHED → QUEUED)."""
    svc = OfflineService(db)
    return OfflineActionResponse.model_validate(svc.promote_to_queue(action_id))


@router.post(
    "/actions/promote-all",
    response_model=OfflinePromoteAllResponse,
    summary="Promote all cached actions",
)
def promote_all(
    node_id: Optional[str] = Query(None, description="Limit to specific node"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OfflinePromoteAllResponse:
    """Bulk-promote all CACHED actions to the sync queue."""
    svc = OfflineService(db)
    count = svc.promote_all_cached(node_id=node_id)
    return OfflinePromoteAllResponse(promoted_count=count)


@router.get(
    "/actions/{action_id}/verify",
    summary="Verify action checksum",
)
def verify_checksum(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Verify the SHA-256 checksum of an offline action's payload."""
    svc = OfflineService(db)
    valid = svc.verify_checksum(action_id)
    return {"action_id": str(action_id), "checksum_valid": valid}
