"""
NAYAM (नयम्) — SyncQueue Repository (Phase 4).

Database operations for the offline-to-central sync queue.
Handles creation, status transitions, retries, and batch queries.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.sync.models import SyncQueue, SyncStatus, SyncOperation

logger = logging.getLogger(__name__)


class SyncQueueRepository:
    """Repository for SyncQueue CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Single Record ────────────────────────────────────────────

    def get_by_id(self, sync_id: UUID) -> Optional[SyncQueue]:
        return self.db.query(SyncQueue).filter(SyncQueue.id == sync_id).first()

    def create(self, entry: SyncQueue) -> SyncQueue:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(
            "Sync entry created: id=%s node=%s op=%s resource=%s:%s",
            entry.id, entry.node_id, entry.operation.value,
            entry.resource_type, entry.resource_id,
        )
        return entry

    # ── Status Transitions ───────────────────────────────────────

    def mark_in_progress(self, entry: SyncQueue) -> SyncQueue:
        entry.status = SyncStatus.IN_PROGRESS
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def mark_synced(self, entry: SyncQueue) -> SyncQueue:
        entry.status = SyncStatus.SYNCED
        entry.synced_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(entry)
        logger.info("Sync entry %s marked SYNCED", entry.id)
        return entry

    def mark_failed(self, entry: SyncQueue, error: str) -> SyncQueue:
        entry.status = SyncStatus.FAILED
        entry.error_message = error
        entry.retry_count += 1
        self.db.commit()
        self.db.refresh(entry)
        logger.warning("Sync entry %s FAILED (retry %d): %s", entry.id, entry.retry_count, error)
        return entry

    def mark_conflict(self, entry: SyncQueue) -> SyncQueue:
        entry.status = SyncStatus.CONFLICT
        self.db.commit()
        self.db.refresh(entry)
        return entry

    # ── Listing / Filtering ──────────────────────────────────────

    def get_pending(
        self,
        node_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SyncQueue], int]:
        query = self.db.query(SyncQueue).filter(SyncQueue.status == SyncStatus.PENDING)
        if node_id:
            query = query.filter(SyncQueue.node_id == node_id)
        total = query.count()
        items = query.order_by(SyncQueue.priority.asc(), SyncQueue.created_at.asc()).offset(skip).limit(limit).all()
        return items, total

    def get_retryable(self, max_retries: int = 3) -> List[SyncQueue]:
        """Get failed entries that haven't exceeded retry limit."""
        return (
            self.db.query(SyncQueue)
            .filter(
                SyncQueue.status == SyncStatus.FAILED,
                SyncQueue.retry_count < max_retries,
            )
            .order_by(SyncQueue.priority.asc())
            .all()
        )

    def get_by_node(self, node_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[SyncQueue], int]:
        query = self.db.query(SyncQueue).filter(SyncQueue.node_id == node_id)
        total = query.count()
        items = query.order_by(SyncQueue.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_resource(self, resource_type: str, resource_id: UUID) -> List[SyncQueue]:
        return (
            self.db.query(SyncQueue)
            .filter(SyncQueue.resource_type == resource_type, SyncQueue.resource_id == resource_id)
            .order_by(SyncQueue.version.desc())
            .all()
        )

    def count_by_status(self) -> List[Tuple[str, int]]:
        from sqlalchemy import func
        return (
            self.db.query(SyncQueue.status, func.count(SyncQueue.id))
            .group_by(SyncQueue.status)
            .all()
        )

    def delete(self, entry: SyncQueue) -> None:
        self.db.delete(entry)
        self.db.commit()
        logger.info("Sync entry deleted: %s", entry.id)
