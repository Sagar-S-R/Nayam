"""
NAYAM (नयम्) — SyncQueue ORM Model (Phase 4).

Stores offline operations queued for synchronisation with the central
server.  Each record represents a single create/update/delete action
performed while the edge node was disconnected.

Flow:  Edge Client (offline) → Local Storage → SyncQueue → Secure API → Backend
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Index, Integer, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base


class SyncOperation(str, enum.Enum):
    """Type of data operation that was queued offline."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatus(str, enum.Enum):
    """Lifecycle state of a queued sync item."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncQueue(Base):
    """
    Offline operation queue entry.

    Attributes:
        id:               UUID primary key.
        node_id:          Identifier of the originating edge node.
        operation:        CREATE / UPDATE / DELETE.
        resource_type:    Target entity (e.g. "issue", "citizen").
        resource_id:      UUID of the affected record.
        payload:          Serialised data snapshot (JSON).
        version:          Monotonic version counter for ordering.
        status:           Current sync lifecycle state.
        priority:         Sync priority (lower = higher priority).
        retry_count:      Number of failed sync attempts.
        max_retries:      Ceiling on automatic retries.
        error_message:    Last failure reason (if any).
        checksum:         SHA-256 of payload for integrity verification.
        created_at:       When the operation was queued offline.
        synced_at:        When the operation was successfully applied.
    """

    __tablename__ = "sync_queue"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    node_id = Column(String(100), nullable=False)
    operation = Column(
        Enum(SyncOperation, name="sync_operation_enum", native_enum=False),
        nullable=False,
    )
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Uuid, nullable=False)
    payload = Column(JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(
        Enum(SyncStatus, name="sync_status_enum", native_enum=False),
        nullable=False,
        default=SyncStatus.PENDING,
    )
    priority = Column(Integer, nullable=False, default=5)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    error_message = Column(Text, nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256 hex
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    synced_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sync_queue_node_id", "node_id"),
        Index("ix_sync_queue_status", "status"),
        Index("ix_sync_queue_resource", "resource_type", "resource_id"),
        Index("ix_sync_queue_priority", "priority"),
        Index("ix_sync_queue_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SyncQueue(node={self.node_id}, op={self.operation}, "
            f"resource={self.resource_type}:{self.resource_id}, "
            f"status={self.status})>"
        )
