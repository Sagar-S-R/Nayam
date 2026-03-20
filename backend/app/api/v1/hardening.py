"""
NAYAM (नयम्) — Hardening API Routes (Phase 4).

Endpoints for rate-limit audit, security reports, and top-offenders.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.hardening import (
    RateLimitRecordResponse,
    RateLimitListResponse,
    RateLimitSummaryResponse,
    TopOffenderEntry,
    TopOffendersResponse,
)
from app.hardening.repository import RateLimitRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/rate-limits",
    response_model=RateLimitListResponse,
    summary="List rate-limit events",
)
def list_rate_limits(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> RateLimitListResponse:
    """List all rate-limit events (admin-only)."""
    repo = RateLimitRepository(db)
    # Reuse get_blocked for filtered, or direct query for all
    from app.hardening.models import RateLimitRecord
    query = db.query(RateLimitRecord)
    total = query.count()
    records = query.order_by(RateLimitRecord.created_at.desc()).offset(skip).limit(limit).all()
    return RateLimitListResponse(
        total=total,
        records=[RateLimitRecordResponse.model_validate(r) for r in records],
    )


@router.get(
    "/rate-limits/blocked",
    response_model=RateLimitListResponse,
    summary="List blocked requests",
)
def list_blocked(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> RateLimitListResponse:
    """List only blocked rate-limit events."""
    repo = RateLimitRepository(db)
    records, total = repo.get_blocked(skip=skip, limit=limit)
    return RateLimitListResponse(
        total=total,
        records=[RateLimitRecordResponse.model_validate(r) for r in records],
    )


@router.get(
    "/rate-limits/summary",
    response_model=RateLimitSummaryResponse,
    summary="Rate-limit summary",
)
def rate_limit_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> RateLimitSummaryResponse:
    """Overview of rate-limit events: total and blocked counts."""
    repo = RateLimitRepository(db)
    return RateLimitSummaryResponse(
        total_events=repo.total_count(),
        total_blocked=repo.count_blocked(),
    )


@router.get(
    "/rate-limits/top-offenders",
    response_model=TopOffendersResponse,
    summary="Top rate-limited IPs",
)
def top_offenders(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> TopOffendersResponse:
    """Return the IPs with the most blocked requests."""
    repo = RateLimitRepository(db)
    rows = repo.get_top_offenders(limit=limit)
    return TopOffendersResponse(
        offenders=[TopOffenderEntry(client_ip=ip, blocked_count=cnt) for ip, cnt in rows],
    )
