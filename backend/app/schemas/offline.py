"""
NAYAM (नयम्) — Offline Pydantic Schemas (Phase 4).

Request / response models for offline action caching and promotion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.offline.models import OfflineStatus


class OfflineCacheRequest(BaseModel):
    """Request body to cache an offline action."""
    node_id: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[UUID] = None
    action_type: str = Field(..., min_length=1, max_length=100)
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[UUID] = None
    payload: Optional[Dict[str, Any]] = None


class OfflineActionResponse(BaseModel):
    """Single offline action in responses."""
    id: UUID
    node_id: str
    user_id: Optional[UUID]
    action_type: str
    resource_type: str
    resource_id: Optional[UUID]
    payload: Optional[Dict[str, Any]]
    status: OfflineStatus
    checksum: Optional[str]
    created_at: datetime
    queued_at: Optional[datetime]

    model_config = {"from_attributes": True}


class OfflineListResponse(BaseModel):
    """Paginated offline action list."""
    total: int
    actions: List[OfflineActionResponse]


class OfflineStatusSummaryResponse(BaseModel):
    """Counts by offline action status."""
    summary: Dict[str, int]


class OfflinePromoteAllResponse(BaseModel):
    """Result of bulk promotion."""
    promoted_count: int
