"""
NAYAM (नयम्) — ConflictLog ORM Model (Phase 4).

Records sync conflicts that arise when offline mutations collide with
central-server state.  Provides the data needed for manual or automatic
conflict resolution.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Index, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ConflictResolution(str, enum.Enum):
    """How the conflict was (or will be) resolved."""
    PENDING = "pending"
    LOCAL_WINS = "local_wins"
    SERVER_WINS = "server_wins"
    MERGED = "merged"
    MANUAL = "manual"


class ConflictLog(Base):
    """
    Sync conflict record.

    Attributes:
        id:               UUID primary key.
        sync_queue_id:    FK to the SyncQueue entry that triggered the conflict.
        node_id:          Edge node where the conflict originated.
        resource_type:    Entity type that conflicted.
        resource_id:      UUID of the conflicting record.
        local_data:       Data from the offline node (JSON).
        server_data:      Data currently on the central server (JSON).
        resolution:       How the conflict was resolved.
        resolved_by:      UUID of the user who resolved (nullable for auto).
        resolution_notes: Free-text explanation.
        detected_at:      When the conflict was detected.
        resolved_at:      When the conflict was resolved.
    """

    __tablename__ = "conflict_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    sync_queue_id = Column(
        Uuid,
        ForeignKey("sync_queue.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    node_id = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Uuid, nullable=False)
    local_data = Column(JSON, nullable=True)
    server_data = Column(JSON, nullable=True)
    resolution = Column(
        Enum(ConflictResolution, name="conflict_resolution_enum", native_enum=False),
        nullable=False,
        default=ConflictResolution.PENDING,
    )
    resolved_by = Column(Uuid, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────
    sync_entry = relationship("SyncQueue", foreign_keys=[sync_queue_id], lazy="select")

    __table_args__ = (
        Index("ix_conflict_logs_node_id", "node_id"),
        Index("ix_conflict_logs_resource", "resource_type", "resource_id"),
        Index("ix_conflict_logs_resolution", "resolution"),
        Index("ix_conflict_logs_detected_at", "detected_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConflictLog(node={self.node_id}, resource={self.resource_type}:"
            f"{self.resource_id}, resolution={self.resolution})>"
        )
