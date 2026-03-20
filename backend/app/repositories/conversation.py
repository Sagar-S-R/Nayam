"""
NAYAM (नयम्) — Conversation Repository (Phase 2).

Handles all database operations for the Conversation model.
Supports session-based history retrieval and user context lookups.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, MessageRole

logger = logging.getLogger(__name__)


class ConversationRepository:
    """
    Repository for Conversation CRUD operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Single Record ────────────────────────────────────────────

    def get_by_id(self, message_id: UUID) -> Optional[Conversation]:
        """
        Retrieve a single conversation message by its UUID.

        Args:
            message_id: The UUID of the message.

        Returns:
            Conversation object or None.
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == message_id)
            .first()
        )

    def create(self, message: Conversation) -> Conversation:
        """
        Persist a new conversation message.

        Args:
            message: The Conversation ORM instance.

        Returns:
            The persisted message with generated ID.
        """
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        logger.info(
            "Stored conversation message: session=%s role=%s agent=%s",
            message.session_id, message.role, message.agent_name,
        )
        return message

    def create_many(self, messages: List[Conversation]) -> List[Conversation]:
        """
        Persist multiple conversation messages in one transaction.

        Args:
            messages: List of Conversation ORM instances.

        Returns:
            The persisted messages.
        """
        self.db.add_all(messages)
        self.db.commit()
        for m in messages:
            self.db.refresh(m)
        logger.info("Stored %d conversation messages", len(messages))
        return messages

    # ── Session History ──────────────────────────────────────────

    def get_session_history(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Conversation]:
        """
        Retrieve all messages in a conversation session, ordered by time.

        Args:
            session_id: UUID of the conversation session.
            limit: Optional cap on number of messages (most recent).

        Returns:
            Ordered list of Conversation objects.
        """
        query = (
            self.db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.asc())
        )
        if limit:
            # Get the *last* N messages by using a subquery approach
            query = (
                self.db.query(Conversation)
                .filter(Conversation.session_id == session_id)
                .order_by(Conversation.created_at.desc())
                .limit(limit)
            )
            results = query.all()
            results.reverse()
            return results
        return query.all()

    def count_session_messages(self, session_id: UUID) -> int:
        """
        Count messages in a conversation session.

        Args:
            session_id: UUID of the conversation session.

        Returns:
            Integer count.
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .count()
        )

    # ── User Lookups ─────────────────────────────────────────────

    def get_user_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[UUID]:
        """
        Retrieve distinct session IDs for a user, most recent first.

        Args:
            user_id: UUID of the user.
            skip: Offset.
            limit: Max results.

        Returns:
            List of session UUIDs.
        """
        rows = (
            self.db.query(Conversation.session_id)
            .filter(Conversation.user_id == user_id)
            .group_by(Conversation.session_id)
            .order_by(func.max(Conversation.created_at).desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]

    def get_user_recent_messages(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> List[Conversation]:
        """
        Retrieve the most recent messages across all sessions for a user.

        Args:
            user_id: UUID of the user.
            limit: Max results.

        Returns:
            List of Conversation objects, most recent first.
        """
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )

    # ── Deletion ─────────────────────────────────────────────────

    def delete_session(self, session_id: UUID) -> int:
        """
        Delete all messages in a conversation session.

        Args:
            session_id: UUID of the session to delete.

        Returns:
            Number of deleted rows.
        """
        count = (
            self.db.query(Conversation)
            .filter(Conversation.session_id == session_id)
            .delete(synchronize_session="fetch")
        )
        self.db.commit()
        logger.info("Deleted %d messages from session %s", count, session_id)
        return count
