"""
NAYAM (नयम्) — Hardening Pydantic Schemas (Phase 4).

Request / response models for rate-limit audit and security endpoints.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel


class RateLimitRecordResponse(BaseModel):
    """Single rate-limit event in responses."""
    id: UUID
    client_ip: str
    user_id: Optional[UUID]
    endpoint: str
    request_count: int
    window_seconds: int
    blocked: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RateLimitListResponse(BaseModel):
    """Paginated rate-limit records."""
    total: int
    records: List[RateLimitRecordResponse]


class RateLimitSummaryResponse(BaseModel):
    """Rate-limit audit summary."""
    total_events: int
    total_blocked: int


class TopOffenderEntry(BaseModel):
    """Single top-offender IP entry."""
    client_ip: str
    blocked_count: int


class TopOffendersResponse(BaseModel):
    """Top rate-limited IPs."""
    offenders: List[TopOffenderEntry]
