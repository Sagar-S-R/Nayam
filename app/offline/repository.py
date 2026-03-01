"""
NAYAM (नयम्) — OfflineAction Repository (Phase 4).

Database operations for locally-cached offline operations.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.offline.models import OfflineAction, OfflineStatus

logger = logging.getLogger(__name__)


class OfflineActionRepository:
    """Repository for OfflineAction CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, action_id: UUID) -> Optional[OfflineAction]:
        return self.db.query(OfflineAction).filter(OfflineAction.id == action_id).first()

    def create(self, action: OfflineAction) -> OfflineAction:
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        logger.info(
            "Offline action cached: id=%s node=%s type=%s resource=%s",
            action.id, action.node_id, action.action_type, action.resource_type,
        )
        return action

    def mark_queued(self, action: OfflineAction) -> OfflineAction:
        action.status = OfflineStatus.QUEUED
        action.queued_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)
        return action

    def mark_synced(self, action: OfflineAction) -> OfflineAction:
        action.status = OfflineStatus.SYNCED
        self.db.commit()
        self.db.refresh(action)
        return action

    def mark_failed(self, action: OfflineAction) -> OfflineAction:
        action.status = OfflineStatus.FAILED
        self.db.commit()
        self.db.refresh(action)
        return action

    def get_cached(
        self,
        node_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[OfflineAction], int]:
        query = self.db.query(OfflineAction).filter(OfflineAction.status == OfflineStatus.CACHED)
        if node_id:
            query = query.filter(OfflineAction.node_id == node_id)
        total = query.count()
        items = query.order_by(OfflineAction.created_at.asc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_node(self, node_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[OfflineAction], int]:
        query = self.db.query(OfflineAction).filter(OfflineAction.node_id == node_id)
        total = query.count()
        items = query.order_by(OfflineAction.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_user(self, user_id: UUID) -> List[OfflineAction]:
        return (
            self.db.query(OfflineAction)
            .filter(OfflineAction.user_id == user_id)
            .order_by(OfflineAction.created_at.desc())
            .all()
        )

    def count_by_status(self) -> List[Tuple[str, int]]:
        from sqlalchemy import func
        return (
            self.db.query(OfflineAction.status, func.count(OfflineAction.id))
            .group_by(OfflineAction.status)
            .all()
        )

    def delete(self, action: OfflineAction) -> None:
        self.db.delete(action)
        self.db.commit()
