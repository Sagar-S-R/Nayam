"""
NAYAM (नयम्) — RateLimitRecord Repository (Phase 4).

Database operations for rate-limit event logging.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.hardening.models import RateLimitRecord

logger = logging.getLogger(__name__)


class RateLimitRepository:
    """Repository for RateLimitRecord CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, record_id: UUID) -> Optional[RateLimitRecord]:
        return self.db.query(RateLimitRecord).filter(RateLimitRecord.id == record_id).first()

    def create(self, record: RateLimitRecord) -> RateLimitRecord:
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_ip(
        self,
        client_ip: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[RateLimitRecord], int]:
        query = self.db.query(RateLimitRecord).filter(RateLimitRecord.client_ip == client_ip)
        total = query.count()
        items = query.order_by(RateLimitRecord.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_blocked(self, skip: int = 0, limit: int = 50) -> Tuple[List[RateLimitRecord], int]:
        query = self.db.query(RateLimitRecord).filter(RateLimitRecord.blocked == 1)
        total = query.count()
        items = query.order_by(RateLimitRecord.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def count_by_ip(self, client_ip: str, since: datetime) -> int:
        """Count requests from an IP since a given time."""
        return (
            self.db.query(RateLimitRecord)
            .filter(
                RateLimitRecord.client_ip == client_ip,
                RateLimitRecord.created_at >= since,
            )
            .count()
        )

    def count_blocked(self) -> int:
        return self.db.query(RateLimitRecord).filter(RateLimitRecord.blocked == 1).count()

    def total_count(self) -> int:
        return self.db.query(RateLimitRecord).count()

    def get_top_offenders(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Return IPs with most blocked requests."""
        return (
            self.db.query(
                RateLimitRecord.client_ip,
                func.count(RateLimitRecord.id).label("blocked_count"),
            )
            .filter(RateLimitRecord.blocked == 1)
            .group_by(RateLimitRecord.client_ip)
            .order_by(func.count(RateLimitRecord.id).desc())
            .limit(limit)
            .all()
        )

    def delete(self, record: RateLimitRecord) -> None:
        self.db.delete(record)
        self.db.commit()
