"""
NAYAM (नयम्) — ActionRequest ORM Model (Phase 2).

Implements the Human-in-the-Loop approval workflow.
Every AI-generated action that mutates state must be recorded here
and explicitly approved or rejected by an authorized user before execution.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActionStatus(str, enum.Enum):
    """Lifecycle states for an AI-generated action request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionRequest(Base):
    """
    ActionRequest ORM model.

    Attributes:
        id: UUID primary key.
        session_id: Conversation session that triggered this action.
        agent_name: Agent that proposed the action.
        action_type: Semantic label (e.g. "update_issue_status", "assign_department").
        description: Human-readable explanation of the proposed action.
        payload: JSON dict containing the full action parameters.
        status: Current lifecycle state.
        requested_by: FK to the user whose session triggered the action.
        reviewed_by: FK to the user who approved / rejected (nullable until reviewed).
        review_note: Optional reviewer comment.
        created_at: When the action was proposed.
        reviewed_at: When the action was approved / rejected.
    """

    __tablename__ = "action_requests"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    session_id = Column(Uuid, nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    action_type = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(
        Enum(ActionStatus, name="action_status_enum", native_enum=False),
        nullable=False,
        default=ActionStatus.PENDING,
    )
    requested_by = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewed_by = Column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    review_note = Column(Text, nullable=True, default=None)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # ── Relationships ────────────────────────────────────────────
    requester = relationship(
        "User",
        foreign_keys=[requested_by],
        lazy="select",
    )
    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        lazy="select",
    )

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_action_requests_status", "status"),
        Index("ix_action_requests_agent", "agent_name"),
        Index("ix_action_requests_created_at", "created_at"),
        Index("ix_action_requests_session_status", "session_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ActionRequest(id={self.id}, agent={self.agent_name}, "
            f"type={self.action_type}, status={self.status})>"
        )
