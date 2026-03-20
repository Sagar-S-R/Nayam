"""
NAYAM (नयम्) — ConflictLog Repository (Phase 4).

Database operations for sync conflict tracking and resolution.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.sync.conflict_model import ConflictLog, ConflictResolution

logger = logging.getLogger(__name__)


class ConflictLogRepository:
    """Repository for ConflictLog CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, conflict_id: UUID) -> Optional[ConflictLog]:
        return self.db.query(ConflictLog).filter(ConflictLog.id == conflict_id).first()

    def create(self, conflict: ConflictLog) -> ConflictLog:
        self.db.add(conflict)
        self.db.commit()
        self.db.refresh(conflict)
        logger.info(
            "Conflict logged: id=%s node=%s resource=%s:%s",
            conflict.id, conflict.node_id, conflict.resource_type, conflict.resource_id,
        )
        return conflict

    def resolve(
        self,
        conflict: ConflictLog,
        resolution: ConflictResolution,
        resolved_by: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> ConflictLog:
        conflict.resolution = resolution
        conflict.resolved_by = resolved_by
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolution_notes = notes
        self.db.commit()
        self.db.refresh(conflict)
        logger.info("Conflict %s resolved → %s", conflict.id, resolution.value)
        return conflict

    def get_pending(self, skip: int = 0, limit: int = 50) -> Tuple[List[ConflictLog], int]:
        query = self.db.query(ConflictLog).filter(ConflictLog.resolution == ConflictResolution.PENDING)
        total = query.count()
        items = query.order_by(ConflictLog.detected_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_node(self, node_id: str) -> List[ConflictLog]:
        return (
            self.db.query(ConflictLog)
            .filter(ConflictLog.node_id == node_id)
            .order_by(ConflictLog.detected_at.desc())
            .all()
        )

    def get_by_sync_entry(self, sync_queue_id: UUID) -> Optional[ConflictLog]:
        return (
            self.db.query(ConflictLog)
            .filter(ConflictLog.sync_queue_id == sync_queue_id)
            .first()
        )

    def pending_count(self) -> int:
        return (
            self.db.query(ConflictLog)
            .filter(ConflictLog.resolution == ConflictResolution.PENDING)
            .count()
        )

    def delete(self, conflict: ConflictLog) -> None:
        self.db.delete(conflict)
        self.db.commit()
