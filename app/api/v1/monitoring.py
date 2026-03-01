"""
NAYAM (नयम्) — Monitoring API Routes (Phase 4).

Endpoints for performance metrics recording, querying,
and deep health probes.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.monitoring.models import MetricCategory
from app.schemas.monitoring import (
    MetricRecordRequest,
    MetricResponse,
    MetricListResponse,
    HealthProbeResponse,
    AverageLatencyResponse,
)
from app.monitoring.service import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/metrics",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a performance metric",
)
def record_metric(
    payload: MetricRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricResponse:
    """Record a single performance measurement."""
    svc = MonitoringService(db)
    metric = svc.record_metric(
        category=payload.category,
        value=payload.value,
        unit=payload.unit,
        endpoint=payload.endpoint,
        method=payload.method,
        status_code=payload.status_code,
        node_id=payload.node_id,
        metadata_json=payload.metadata_json,
    )
    return MetricResponse.model_validate(metric)


@router.get(
    "/metrics",
    response_model=MetricListResponse,
    summary="List recent metrics",
)
def list_metrics(
    category: Optional[MetricCategory] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricListResponse:
    """List performance metrics with optional category filter."""
    svc = MonitoringService(db)
    if category:
        items, total = svc.list_by_category(category, skip=skip, limit=limit)
    else:
        items = svc.recent_metrics(limit=limit)
        total = len(items)
    return MetricListResponse(
        total=total,
        metrics=[MetricResponse.model_validate(m) for m in items],
    )


@router.get(
    "/metrics/average/{category}",
    response_model=AverageLatencyResponse,
    summary="Average metric by category",
)
def average_metric(
    category: MetricCategory,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AverageLatencyResponse:
    """Get the average value for a metric category."""
    svc = MonitoringService(db)
    avg = svc.average_latency(category)
    return AverageLatencyResponse(category=category, average=avg)


@router.get(
    "/health/deep",
    response_model=HealthProbeResponse,
    summary="Deep health probe",
)
def deep_health(
    db: Session = Depends(get_db),
) -> HealthProbeResponse:
    """
    Deep health check that exercises DB connectivity.

    No authentication required — intended for load-balancer probes.
    """
    svc = MonitoringService(db)
    result = svc.health_check()
    return HealthProbeResponse(**result)
