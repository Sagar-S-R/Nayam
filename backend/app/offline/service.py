"""
NAYAM (नयम्) — Offline Service (Phase 4).

Business logic for local offline action caching and promotion
into the sync queue.

Design references: FR4-001 (offline read/write, sync on reconnect).
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.offline.models import OfflineAction, OfflineStatus
from app.offline.repository import OfflineActionRepository
from app.sync.models import SyncOperation
from app.sync.service import SyncService

logger = logging.getLogger(__name__)


class OfflineService:
    """Manages offline action caching and queue promotion."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OfflineActionRepository(db)
        self.sync_service = SyncService(db)
        self.settings = get_settings()

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def compute_checksum(payload: Optional[dict]) -> str:
        raw = json.dumps(payload or {}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Caching ──────────────────────────────────────────────────

    def cache_action(
        self,
        node_id: str,
        user_id: Optional[UUID],
        action_type: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        payload: Optional[dict] = None,
    ) -> OfflineAction:
        """Store an offline action in the local cache."""
        action = OfflineAction(
            node_id=node_id,
            user_id=user_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            checksum=self.compute_checksum(payload),
        )
        return self.repo.create(action)

    def get_action(self, action_id: UUID) -> OfflineAction:
        action = self.repo.get_by_id(action_id)
        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offline action {action_id} not found",
            )
        return action

    def list_cached(
        self,
        node_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[OfflineAction], int]:
        return self.repo.get_cached(node_id=node_id, skip=skip, limit=limit)

    def list_by_node(
        self, node_id: str, skip: int = 0, limit: int = 50
    ) -> Tuple[List[OfflineAction], int]:
        return self.repo.get_by_node(node_id, skip=skip, limit=limit)

    def list_by_user(self, user_id: UUID) -> List[OfflineAction]:
        return self.repo.get_by_user(user_id)

    def status_summary(self) -> Dict[str, int]:
        rows = self.repo.count_by_status()
        return {s.value if hasattr(s, "value") else str(s): c for s, c in rows}

    # ── Queue Promotion ──────────────────────────────────────────

    def _map_action_to_operation(self, action_type: str) -> SyncOperation:
        """Infer SyncOperation from the action_type string."""
        lower = action_type.lower()
        if "create" in lower or "add" in lower:
            return SyncOperation.CREATE
        if "delete" in lower or "remove" in lower:
            return SyncOperation.DELETE
        return SyncOperation.UPDATE

    def promote_to_queue(self, action_id: UUID) -> OfflineAction:
        """Move a CACHED action to the sync queue (CACHED → QUEUED)."""
        action = self.get_action(action_id)
        if action.status != OfflineStatus.CACHED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Action is {action.status.value}, expected CACHED",
            )

        # Create a corresponding SyncQueue entry
        operation = self._map_action_to_operation(action.action_type)
        self.sync_service.enqueue(
            node_id=action.node_id,
            operation=operation,
            resource_type=action.resource_type,
            resource_id=action.resource_id or action.id,
            payload=action.payload,
        )

        return self.repo.mark_queued(action)

    def promote_all_cached(self, node_id: Optional[str] = None) -> int:
        """Promote every CACHED action for a node (or all nodes) to QUEUED."""
        cached, _ = self.repo.get_cached(node_id=node_id, limit=10_000)
        promoted = 0
        for action in cached:
            try:
                self.promote_to_queue(action.id)
                promoted += 1
            except HTTPException:
                logger.warning("Skip promotion of action %s", action.id)
        logger.info("Promoted %d cached actions to sync queue", promoted)
        return promoted

    def mark_synced(self, action_id: UUID) -> OfflineAction:
        action = self.get_action(action_id)
        return self.repo.mark_synced(action)

    def mark_failed(self, action_id: UUID) -> OfflineAction:
        action = self.get_action(action_id)
        return self.repo.mark_failed(action)

    # ── Integrity ────────────────────────────────────────────────

    def verify_checksum(self, action_id: UUID) -> bool:
        action = self.get_action(action_id)
        return action.checksum == self.compute_checksum(action.payload)
