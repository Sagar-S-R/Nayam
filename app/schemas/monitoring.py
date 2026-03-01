"""
NAYAM (नयम्) — Monitoring Pydantic Schemas (Phase 4).

Request / response models for performance metrics and health probes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.monitoring.models import MetricCategory


class MetricRecordRequest(BaseModel):
    """Request body to record a performance metric."""
    category: MetricCategory
    value: float = Field(..., ge=0)
    unit: str = Field(default="ms", max_length=20)
    endpoint: Optional[str] = Field(None, max_length=500)
    method: Optional[str] = Field(None, max_length=10)
    status_code: Optional[int] = None
    node_id: Optional[str] = Field(None, max_length=100)
    metadata_json: Optional[Dict[str, Any]] = None


class MetricResponse(BaseModel):
    """Single performance metric in responses."""
    id: UUID
    category: MetricCategory
    endpoint: Optional[str]
    method: Optional[str]
    value: float
    unit: str
    status_code: Optional[int]
    node_id: Optional[str]
    metadata_json: Optional[Dict[str, Any]]
    recorded_at: datetime

    model_config = {"from_attributes": True}


class MetricListResponse(BaseModel):
    """List of performance metrics."""
    total: int
    metrics: List[MetricResponse]


class HealthProbeResponse(BaseModel):
    """Health probe result."""
    status: str
    db_connected: bool
    db_latency_ms: Optional[float] = None
    total_metrics: Optional[int] = None
    performance_tracking_enabled: Optional[bool] = None
    error: Optional[str] = None


class AverageLatencyResponse(BaseModel):
    """Average latency for a metric category."""
    category: MetricCategory
    average: Optional[float]
