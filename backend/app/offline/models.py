"""
NAYAM (नयम्) — OfflineAction ORM Model (Phase 4).

Represents a single offline-cached action (read or write) stored
locally before network connectivity is restored.  Designed to be
consumed by the SyncQueue when the edge node reconnects.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Index, Integer, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base


class OfflineStatus(str, enum.Enum):
    """State of a locally cached offline action."""
    CACHED = "cached"
    QUEUED = "queued"
    SYNCED = "synced"
    FAILED = "failed"


class OfflineAction(Base):
    """
    Locally-cached offline operation.

    Attributes:
        id:              UUID primary key.
        node_id:         Originating edge node identifier.
        user_id:         UUID of the user who performed the action offline.
        action_type:     What the user did (create_issue, update_citizen, etc.).
        resource_type:   Target entity type.
        resource_id:     UUID of the affected record.
        payload:         Full data snapshot (JSON).
        status:          Current lifecycle state.
        checksum:        SHA-256 of payload for integrity.
        created_at:      When the action was performed offline.
        queued_at:       When it was moved to the sync queue.
    """

    __tablename__ = "offline_actions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    node_id = Column(String(100), nullable=False)
    user_id = Column(Uuid, nullable=True)
    action_type = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Uuid, nullable=True)
    payload = Column(JSON, nullable=True)
    status = Column(
        Enum(OfflineStatus, name="offline_status_enum", native_enum=False),
        nullable=False,
        default=OfflineStatus.CACHED,
    )
    checksum = Column(String(64), nullable=True)  # SHA-256 hex
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    queued_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_offline_actions_node_id", "node_id"),
        Index("ix_offline_actions_user_id", "user_id"),
        Index("ix_offline_actions_status", "status"),
        Index("ix_offline_actions_resource", "resource_type"),
        Index("ix_offline_actions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<OfflineAction(node={self.node_id}, action={self.action_type}, "
            f"resource={self.resource_type}, status={self.status})>"
        )
