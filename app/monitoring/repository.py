"""
NAYAM (नयम्) — PerformanceMetric Repository (Phase 4).

Database operations for performance metrics collection and querying.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.monitoring.models import PerformanceMetric, MetricCategory

logger = logging.getLogger(__name__)


class PerformanceMetricRepository:
    """Repository for PerformanceMetric CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, metric_id: UUID) -> Optional[PerformanceMetric]:
        return self.db.query(PerformanceMetric).filter(PerformanceMetric.id == metric_id).first()

    def create(self, metric: PerformanceMetric) -> PerformanceMetric:
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def create_batch(self, metrics: List[PerformanceMetric]) -> List[PerformanceMetric]:
        self.db.add_all(metrics)
        self.db.commit()
        for m in metrics:
            self.db.refresh(m)
        return metrics

    def get_by_category(
        self,
        category: MetricCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[PerformanceMetric], int]:
        query = self.db.query(PerformanceMetric).filter(PerformanceMetric.category == category)
        total = query.count()
        items = query.order_by(PerformanceMetric.recorded_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_endpoint(self, endpoint: str, limit: int = 50) -> List[PerformanceMetric]:
        return (
            self.db.query(PerformanceMetric)
            .filter(PerformanceMetric.endpoint == endpoint)
            .order_by(PerformanceMetric.recorded_at.desc())
            .limit(limit)
            .all()
        )

    def get_recent(self, limit: int = 100) -> List[PerformanceMetric]:
        return (
            self.db.query(PerformanceMetric)
            .order_by(PerformanceMetric.recorded_at.desc())
            .limit(limit)
            .all()
        )

    def average_by_category(self, category: MetricCategory) -> Optional[float]:
        from sqlalchemy import func
        result = (
            self.db.query(func.avg(PerformanceMetric.value))
            .filter(PerformanceMetric.category == category)
            .scalar()
        )
        return float(result) if result is not None else None

    def total_count(self) -> int:
        return self.db.query(PerformanceMetric).count()

    def delete(self, metric: PerformanceMetric) -> None:
        self.db.delete(metric)
        self.db.commit()
