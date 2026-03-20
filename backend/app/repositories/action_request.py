"""
NAYAM (नयम्) — ActionRequest Repository (Phase 2).

Handles all database operations for the Human-in-the-Loop
ActionRequest model: creation, review, listing, and filtering.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.action_request import ActionRequest, ActionStatus

logger = logging.getLogger(__name__)


class ActionRequestRepository:
    """
    Repository for ActionRequest CRUD operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Single Record ────────────────────────────────────────────

    def get_by_id(self, action_id: UUID) -> Optional[ActionRequest]:
        """
        Retrieve an action request by its UUID.

        Args:
            action_id: The UUID of the action request.

        Returns:
            ActionRequest object or None.
        """
        return (
            self.db.query(ActionRequest)
            .filter(ActionRequest.id == action_id)
            .first()
        )

    def create(self, action: ActionRequest) -> ActionRequest:
        """
        Persist a new action request.

        Args:
            action: The ActionRequest ORM instance.

        Returns:
            The persisted ActionRequest with generated ID.
        """
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        logger.info(
            "Created action request: id=%s agent=%s type=%s",
            action.id, action.agent_name, action.action_type,
        )
        return action

    # ── Review (Approve / Reject) ────────────────────────────────

    def review(
        self,
        action: ActionRequest,
        status: ActionStatus,
        reviewer_id: UUID,
        review_note: Optional[str] = None,
    ) -> ActionRequest:
        """
        Approve or reject an action request.

        Args:
            action: The ActionRequest ORM instance to update.
            status: New status (APPROVED or REJECTED).
            reviewer_id: UUID of the reviewing user.
            review_note: Optional comment from the reviewer.

        Returns:
            The updated ActionRequest.
        """
        action.status = status
        action.reviewed_by = reviewer_id
        action.reviewed_at = datetime.now(timezone.utc)
        action.review_note = review_note
        self.db.commit()
        self.db.refresh(action)
        logger.info(
            "Reviewed action request %s → %s by user %s",
            action.id, status.value, reviewer_id,
        )
        return action

    # ── Listing / Filtering ──────────────────────────────────────

    def get_pending(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ActionRequest], int]:
        """
        Retrieve pending action requests (awaiting review).

        Args:
            skip: Offset.
            limit: Max results.

        Returns:
            Tuple of (list of pending actions, total pending count).
        """
        query = (
            self.db.query(ActionRequest)
            .filter(ActionRequest.status == ActionStatus.PENDING)
        )
        total = query.count()
        actions = (
            query.order_by(ActionRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return actions, total

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ActionStatus] = None,
        agent_name: Optional[str] = None,
    ) -> Tuple[List[ActionRequest], int]:
        """
        Retrieve a paginated, filtered list of action requests.

        Args:
            skip: Offset.
            limit: Max results.
            status: Optional status filter.
            agent_name: Optional agent name filter.

        Returns:
            Tuple of (list of actions, total count).
        """
        query = self.db.query(ActionRequest)
        if status:
            query = query.filter(ActionRequest.status == status)
        if agent_name:
            query = query.filter(ActionRequest.agent_name == agent_name)

        total = query.count()
        actions = (
            query.order_by(ActionRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return actions, total

    def get_by_session(self, session_id: UUID) -> List[ActionRequest]:
        """
        Retrieve all action requests triggered by a conversation session.

        Args:
            session_id: UUID of the conversation session.

        Returns:
            List of ActionRequest objects.
        """
        return (
            self.db.query(ActionRequest)
            .filter(ActionRequest.session_id == session_id)
            .order_by(ActionRequest.created_at.desc())
            .all()
        )

    def get_by_requester(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ActionRequest], int]:
        """
        Retrieve action requests initiated by a specific user.

        Args:
            user_id: UUID of the requesting user.
            skip: Offset.
            limit: Max results.

        Returns:
            Tuple of (list of actions, total count).
        """
        query = (
            self.db.query(ActionRequest)
            .filter(ActionRequest.requested_by == user_id)
        )
        total = query.count()
        actions = (
            query.order_by(ActionRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return actions, total

    # ── Aggregation ──────────────────────────────────────────────

    def count_by_status(self) -> List[Tuple[str, int]]:
        """
        Count action requests grouped by status.

        Returns:
            List of (status, count) tuples.
        """
        from sqlalchemy import func
        return (
            self.db.query(ActionRequest.status, func.count(ActionRequest.id))
            .group_by(ActionRequest.status)
            .all()
        )

    def pending_count(self) -> int:
        """
        Get the number of pending action requests.

        Returns:
            Integer count.
        """
        return (
            self.db.query(ActionRequest)
            .filter(ActionRequest.status == ActionStatus.PENDING)
            .count()
        )

    # ── Deletion ─────────────────────────────────────────────────

    def delete(self, action: ActionRequest) -> None:
        """
        Delete an action request record.

        Args:
            action: The ActionRequest ORM instance to delete.
        """
        self.db.delete(action)
        self.db.commit()
        logger.info("Deleted action request: %s", action.id)
