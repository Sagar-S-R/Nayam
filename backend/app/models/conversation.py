"""
NAYAM (नयम्) — Conversation ORM Model (Phase 2).

Stores multi-turn conversation history between users and AI agents.
Each row is a single message in a conversation session.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageRole(str, enum.Enum):
    """Role of the message sender in a conversation turn."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """
    Conversation ORM model.

    Attributes:
        id: UUID primary key.
        session_id: Groups messages belonging to the same conversation session.
        user_id: FK to the user who initiated the conversation.
        role: Who sent this message (user / assistant / system).
        content: The message text content.
        agent_name: Which agent handled this turn (nullable for user messages).
        created_at: Timestamp of the message.
    """

    __tablename__ = "conversations"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    session_id = Column(
        Uuid,
        nullable=False,
        index=True,
    )
    user_id = Column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(
        Enum(MessageRole, name="message_role_enum", native_enum=False),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    agent_name = Column(String(100), nullable=True, default=None)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    user = relationship("User", lazy="select")

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_conversations_session_created", "session_id", "created_at"),
        Index("ix_conversations_user_session", "user_id", "session_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, session={self.session_id}, "
            f"role={self.role}, agent={self.agent_name})>"
        )
