"""
NAYAM (नयम्) — Monitoring Service (Phase 4).

Business logic for performance metrics recording, querying, and
system health probing.

Design references: FR4-005, NFR (99.5%+ uptime, sync < 3s).
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.monitoring.models import PerformanceMetric, MetricCategory
from app.monitoring.repository import PerformanceMetricRepository

logger = logging.getLogger(__name__)


class MonitoringService:
    """Records and queries performance metrics; provides health probes."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PerformanceMetricRepository(db)
        self.settings = get_settings()

    # ── Recording ────────────────────────────────────────────────

    def record_metric(
        self,
        category: MetricCategory,
        value: float,
        unit: str = "ms",
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        node_id: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> PerformanceMetric:
        """Record a single performance measurement."""
        metric = PerformanceMetric(
            category=category,
            value=value,
            unit=unit,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            node_id=node_id,
            metadata_json=metadata_json,
        )
        return self.repo.create(metric)

    def record_api_latency(
        self,
        endpoint: str,
        method: str,
        latency_ms: float,
        status_code: int,
        node_id: Optional[str] = None,
    ) -> PerformanceMetric:
        """Convenience wrapper to record API latency."""
        return self.record_metric(
            category=MetricCategory.API_LATENCY,
            value=latency_ms,
            unit="ms",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            node_id=node_id,
        )

    def record_sync_latency(
        self,
        latency_ms: float,
        node_id: str,
        metadata_json: Optional[dict] = None,
    ) -> PerformanceMetric:
        """Convenience wrapper to record sync latency."""
        return self.record_metric(
            category=MetricCategory.SYNC_LATENCY,
            value=latency_ms,
            unit="ms",
            node_id=node_id,
            metadata_json=metadata_json,
        )

    # ── Queries ──────────────────────────────────────────────────

    def get_metric(self, metric_id: UUID) -> Optional[PerformanceMetric]:
        return self.repo.get_by_id(metric_id)

    def list_by_category(
        self,
        category: MetricCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PerformanceMetric], int]:
        return self.repo.get_by_category(category, skip=skip, limit=limit)

    def list_by_endpoint(self, endpoint: str, limit: int = 50) -> List[PerformanceMetric]:
        return self.repo.get_by_endpoint(endpoint, limit=limit)

    def recent_metrics(self, limit: int = 100) -> List[PerformanceMetric]:
        return self.repo.get_recent(limit=limit)

    def average_latency(self, category: MetricCategory) -> Optional[float]:
        return self.repo.average_by_category(category)

    # ── Health Probe ─────────────────────────────────────────────

    def health_check(self) -> Dict:
        """
        Return a health-probe payload compatible with /health endpoints.
        Exercises a trivial DB query to confirm connectivity.
        """
        start = time.monotonic()
        try:
            total = self.repo.total_count()
            db_latency_ms = (time.monotonic() - start) * 1000
            return {
                "status": "healthy",
                "db_connected": True,
                "db_latency_ms": round(db_latency_ms, 2),
                "total_metrics": total,
                "performance_tracking_enabled": self.settings.ENABLE_PERFORMANCE_TRACKING,
            }
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            return {
                "status": "unhealthy",
                "db_connected": False,
                "error": str(exc),
            }
