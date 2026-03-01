"""
NAYAM (नयम्) — Sync Service (Phase 4).

Business logic for offline→central synchronisation: queue management,
conflict detection, retry orchestration, and checksum verification.

Design references: FR4-001, FR4-002.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.sync.models import SyncQueue, SyncStatus, SyncOperation
from app.sync.conflict_model import ConflictLog, ConflictResolution
from app.sync.repository import SyncQueueRepository
from app.sync.conflict_repository import ConflictLogRepository

logger = logging.getLogger(__name__)


class SyncService:
    """Orchestrates the sync-queue lifecycle."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.queue_repo = SyncQueueRepository(db)
        self.conflict_repo = ConflictLogRepository(db)
        self.settings = get_settings()

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def compute_checksum(payload: Optional[dict]) -> str:
        """SHA-256 hex digest of a JSON-serialised payload."""
        raw = json.dumps(payload or {}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Queue Management ─────────────────────────────────────────

    def enqueue(
        self,
        node_id: str,
        operation: SyncOperation,
        resource_type: str,
        resource_id: UUID,
        payload: Optional[dict] = None,
        priority: int = 5,
    ) -> SyncQueue:
        """Create a new sync-queue entry from an offline operation."""
        checksum = self.compute_checksum(payload)

        # Determine next version for this resource
        existing = self.queue_repo.get_by_resource(resource_type, resource_id)
        next_version = max((e.version for e in existing), default=0) + 1

        entry = SyncQueue(
            node_id=node_id,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            version=next_version,
            priority=priority,
            max_retries=self.settings.SYNC_MAX_RETRIES,
            checksum=checksum,
        )
        return self.queue_repo.create(entry)

    def get_entry(self, sync_id: UUID) -> SyncQueue:
        entry = self.queue_repo.get_by_id(sync_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sync entry {sync_id} not found",
            )
        return entry

    def list_pending(
        self,
        node_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SyncQueue], int]:
        limit = min(limit, self.settings.SYNC_BATCH_SIZE)
        return self.queue_repo.get_pending(node_id=node_id, skip=skip, limit=limit)

    def list_by_node(
        self, node_id: str, skip: int = 0, limit: int = 50
    ) -> Tuple[List[SyncQueue], int]:
        return self.queue_repo.get_by_node(node_id, skip=skip, limit=limit)

    def status_summary(self) -> Dict[str, int]:
        """Return counts keyed by status name."""
        rows = self.queue_repo.count_by_status()
        return {s.value if hasattr(s, "value") else str(s): c for s, c in rows}

    # ── Sync Lifecycle ───────────────────────────────────────────

    def begin_sync(self, sync_id: UUID) -> SyncQueue:
        """Transition PENDING → IN_PROGRESS."""
        entry = self.get_entry(sync_id)
        if entry.status != SyncStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Entry is {entry.status.value}, expected PENDING",
            )
        return self.queue_repo.mark_in_progress(entry)

    def complete_sync(self, sync_id: UUID) -> SyncQueue:
        """Transition IN_PROGRESS → SYNCED."""
        entry = self.get_entry(sync_id)
        if entry.status != SyncStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Entry is {entry.status.value}, expected IN_PROGRESS",
            )
        return self.queue_repo.mark_synced(entry)

    def fail_sync(self, sync_id: UUID, error: str) -> SyncQueue:
        """Transition IN_PROGRESS → FAILED and increment retry counter."""
        entry = self.get_entry(sync_id)
        if entry.status != SyncStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Entry is {entry.status.value}, expected IN_PROGRESS",
            )
        return self.queue_repo.mark_failed(entry, error)

    def retry_failed(self) -> List[SyncQueue]:
        """Move retryable FAILED entries back to PENDING."""
        retryable = self.queue_repo.get_retryable(
            max_retries=self.settings.SYNC_MAX_RETRIES,
        )
        reset: List[SyncQueue] = []
        for entry in retryable:
            entry.status = SyncStatus.PENDING
            self.db.commit()
            self.db.refresh(entry)
            reset.append(entry)
        logger.info("Reset %d failed entries to PENDING for retry", len(reset))
        return reset

    # ── Conflict Handling ────────────────────────────────────────

    def raise_conflict(
        self,
        sync_id: UUID,
        local_data: Optional[dict],
        server_data: Optional[dict],
    ) -> ConflictLog:
        """Flag a sync entry as conflicted and create a ConflictLog."""
        entry = self.get_entry(sync_id)
        self.queue_repo.mark_conflict(entry)

        conflict = ConflictLog(
            sync_queue_id=entry.id,
            node_id=entry.node_id,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            local_data=local_data,
            server_data=server_data,
        )
        return self.conflict_repo.create(conflict)

    def resolve_conflict(
        self,
        conflict_id: UUID,
        resolution: ConflictResolution,
        resolved_by: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> ConflictLog:
        conflict = self.conflict_repo.get_by_id(conflict_id)
        if not conflict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conflict {conflict_id} not found",
            )
        if conflict.resolution != ConflictResolution.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict already resolved",
            )
        return self.conflict_repo.resolve(conflict, resolution, resolved_by, notes)

    def list_pending_conflicts(
        self, skip: int = 0, limit: int = 50
    ) -> Tuple[List[ConflictLog], int]:
        return self.conflict_repo.get_pending(skip=skip, limit=limit)

    def pending_conflict_count(self) -> int:
        return self.conflict_repo.pending_count()

    # ── Integrity ────────────────────────────────────────────────

    def verify_checksum(self, sync_id: UUID) -> bool:
        """Re-compute checksum and compare to stored value."""
        entry = self.get_entry(sync_id)
        expected = self.compute_checksum(entry.payload)
        return entry.checksum == expected
