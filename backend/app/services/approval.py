"""
NAYAM (नयम्) — Approval Service (Phase 2).

Business logic for the Human-in-the-Loop action approval workflow.
Validates permissions, enforces lifecycle rules, and delegates
persistence to the ActionRequestRepository.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.action_request import ActionRequest, ActionStatus
from app.models.user import User, UserRole
from app.repositories.action_request import ActionRequestRepository

logger = logging.getLogger(__name__)
settings = get_settings()

from app.compliance.audit_writer import write_audit
from app.observability.models import AuditAction


class ApprovalService:
    """
    Service layer for action request approval workflow.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.repo = ActionRequestRepository(db)
        self.db = db

    # ── Create ───────────────────────────────────────────────────

    def create_action_request(
        self,
        session_id: UUID,
        agent_name: str,
        action_type: str,
        description: str,
        payload: dict,
        requested_by: UUID,
    ) -> ActionRequest:
        """
        Create a new pending action request proposed by an agent.

        Args:
            session_id: Conversation session that triggered this.
            agent_name: Agent that proposed the action.
            action_type: Semantic action label.
            description: Human-readable explanation.
            payload: Full action parameters.
            requested_by: UUID of the user whose session triggered it.

        Returns:
            The created ActionRequest in PENDING state.
        """
        action = ActionRequest(
            session_id=session_id,
            agent_name=agent_name,
            action_type=action_type,
            description=description,
            payload=payload,
            requested_by=requested_by,
            status=ActionStatus.PENDING,
        )
        created = self.repo.create(action)
        logger.info(
            "Action request created: id=%s type=%s agent=%s",
            created.id, action_type, agent_name,
        )
        return created

    # ── Review ───────────────────────────────────────────────────

    def approve(
        self,
        action_id: UUID,
        reviewer: User,
        review_note: Optional[str] = None,
    ) -> ActionRequest:
        """
        Approve a pending action request.

        Args:
            action_id: UUID of the action to approve.
            reviewer: The user performing the review.
            review_note: Optional comment.

        Returns:
            The approved ActionRequest.

        Raises:
            HTTPException: 404 if not found, 400 if not pending,
                           403 if reviewer lacks permission.
        """
        return self._review(action_id, ActionStatus.APPROVED, reviewer, review_note)

    def reject(
        self,
        action_id: UUID,
        reviewer: User,
        review_note: Optional[str] = None,
    ) -> ActionRequest:
        """
        Reject a pending action request.

        Args:
            action_id: UUID of the action to reject.
            reviewer: The user performing the review.
            review_note: Optional comment.

        Returns:
            The rejected ActionRequest.

        Raises:
            HTTPException: 404 if not found, 400 if not pending,
                           403 if reviewer lacks permission.
        """
        return self._review(action_id, ActionStatus.REJECTED, reviewer, review_note)

    def _review(
        self,
        action_id: UUID,
        new_status: ActionStatus,
        reviewer: User,
        review_note: Optional[str],
    ) -> ActionRequest:
        """
        Internal review logic shared by approve/reject.

        Validates:
          • Action exists
          • Action is currently PENDING
          • Reviewer has Leader or Staff role
          • Action has not expired
        """
        action = self.repo.get_by_id(action_id)
        if action is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action request {action_id} not found.",
            )

        if action.status != ActionStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action request is already {action.status.value}, cannot review.",
            )

        # Role check — only Leaders and Staff may approve/reject
        if reviewer.role not in (UserRole.LEADER, UserRole.STAFF):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to review action requests.",
            )

        # Expiry check
        expiry_threshold = datetime.now(timezone.utc) - timedelta(
            hours=settings.ACTION_EXPIRY_HOURS,
        )
        if action.created_at.replace(tzinfo=timezone.utc) < expiry_threshold:
            # Auto-expire instead of allowing review
            self.repo.review(action, ActionStatus.EXPIRED, reviewer.id, "Auto-expired")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action request has expired and cannot be reviewed.",
            )

        reviewed = self.repo.review(action, new_status, reviewer.id, review_note)
        audit_action = AuditAction.APPROVE if new_status == ActionStatus.APPROVED else AuditAction.REJECT
        write_audit(
            self.db,
            action=audit_action,
            resource_type="action_request",
            resource_id=str(action_id),
            description=(
                f"Action '{action.action_type}' {new_status.value} by {reviewer.email} ({reviewer.role.value})"
                + (f": {review_note}" if review_note else "")
            ),
            user_id=reviewer.id,
        )
        logger.info(
            "Action %s reviewed → %s by user %s",
            action_id, new_status.value, reviewer.id,
        )
        return reviewed

    # ── Listing ──────────────────────────────────────────────────

    def list_pending(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ActionRequest], int]:
        """
        List all pending action requests.

        Args:
            skip: Offset.
            limit: Max results.

        Returns:
            Tuple of (list of actions, total count).
        """
        return self.repo.get_pending(skip=skip, limit=limit)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[ActionStatus] = None,
        agent_name: Optional[str] = None,
    ) -> Tuple[List[ActionRequest], int]:
        """
        List all action requests with optional filters.

        Args:
            skip: Offset.
            limit: Max results.
            status_filter: Optional status filter.
            agent_name: Optional agent name filter.

        Returns:
            Tuple of (list of actions, total count).
        """
        return self.repo.get_all(
            skip=skip, limit=limit, status=status_filter, agent_name=agent_name,
        )

    def get_action(self, action_id: UUID) -> ActionRequest:
        """
        Retrieve a single action request.

        Args:
            action_id: UUID of the action.

        Returns:
            The ActionRequest.

        Raises:
            HTTPException: 404 if not found.
        """
        action = self.repo.get_by_id(action_id)
        if action is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Action request {action_id} not found.",
            )
        return action

    def get_session_actions(self, session_id: UUID) -> List[ActionRequest]:
        """
        Get all actions triggered by a conversation session.

        Args:
            session_id: UUID of the session.

        Returns:
            List of ActionRequest objects.
        """
        return self.repo.get_by_session(session_id)

    def pending_count(self) -> int:
        """Return the number of pending action requests."""
        return self.repo.pending_count()
