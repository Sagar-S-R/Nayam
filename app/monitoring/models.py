"""
NAYAM (नयम्) — PerformanceMetric ORM Model (Phase 4).

Stores timestamped performance measurements for query benchmarking,
system health monitoring, and SLA compliance (NFR: 99.5%+ uptime,
sync < 3s, support 100K+ issues).
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Float, Index, Integer, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base


class MetricCategory(str, enum.Enum):
    """Classification of the measured metric."""
    API_LATENCY = "api_latency"
    DB_QUERY = "db_query"
    SYNC_LATENCY = "sync_latency"
    CACHE_HIT = "cache_hit"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


class PerformanceMetric(Base):
    """
    System performance measurement.

    Attributes:
        id:              UUID primary key.
        category:        What type of metric this is.
        endpoint:        API path or operation name measured.
        method:          HTTP method (GET, POST, etc.) or blank for non-API.
        value:           Measured numeric value (e.g. latency in ms).
        unit:            Measurement unit (ms, bytes, percent, req/s).
        status_code:     HTTP response code (nullable for non-API metrics).
        node_id:         Edge node identifier (nullable for central).
        metadata_json:   Additional context (JSON).
        recorded_at:     When the measurement was taken.
    """

    __tablename__ = "performance_metrics"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    category = Column(
        Enum(MetricCategory, name="metric_category_enum", native_enum=False),
        nullable=False,
    )
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    value = Column(Float, nullable=False, default=0.0)
    unit = Column(String(20), nullable=False, default="ms")
    status_code = Column(Integer, nullable=True)
    node_id = Column(String(100), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    recorded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_perf_metrics_category", "category"),
        Index("ix_perf_metrics_endpoint", "endpoint"),
        Index("ix_perf_metrics_node_id", "node_id"),
        Index("ix_perf_metrics_recorded_at", "recorded_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<PerformanceMetric(category={self.category}, endpoint={self.endpoint}, "
            f"value={self.value}{self.unit}, at={self.recorded_at})>"
        )
