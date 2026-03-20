"""
NAYAM (नयम्) — Issue Repository.

Handles all database operations for the Issue model.
Supports filtering by status, priority, department, and citizen.
"""

import logging
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.issue import Issue, IssueStatus, IssuePriority

logger = logging.getLogger(__name__)


class IssueRepository:
    """
    Repository for Issue CRUD operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, issue_id: UUID) -> Optional[Issue]:
        """
        Retrieve an issue by its UUID.

        Args:
            issue_id: The UUID of the issue.

        Returns:
            Issue object or None.
        """
        return self.db.query(Issue).filter(Issue.id == issue_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[IssueStatus] = None,
        priority: Optional[IssuePriority] = None,
        department: Optional[str] = None,
        citizen_id: Optional[UUID] = None,
        ward: Optional[str] = None,
        overdue: Optional[bool] = None,
    ) -> Tuple[List[Issue], int]:
        """
        Retrieve a paginated, filtered list of issues.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional status filter.
            priority: Optional priority filter.
            department: Optional department filter.
            citizen_id: Optional citizen FK filter.
            ward: Optional ward filter (joins through citizen).
            overdue: Optional overdue filter based on SLA.

        Returns:
            Tuple of (list of issues, total count).
        """
        query = self.db.query(Issue)

        if status:
            query = query.filter(Issue.status == status)
        if priority:
            query = query.filter(Issue.priority == priority)
        if department:
            query = query.filter(Issue.department == department)
        if citizen_id:
            query = query.filter(Issue.citizen_id == citizen_id)
        if ward:
            query = query.join(Citizen, Issue.citizen_id == Citizen.id).filter(Citizen.ward == ward)
        if overdue is not None:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if overdue:
                query = query.filter(Issue.sla_deadline < now, Issue.status != IssueStatus.CLOSED)
            else:
                query = query.filter((Issue.sla_deadline >= now) | (Issue.status == IssueStatus.CLOSED))

        total = query.count()
        issues = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()
        return issues, total

    def create(self, issue: Issue) -> Issue:
        """
        Persist a new issue to the database.

        Args:
            issue: The Issue ORM instance.

        Returns:
            The persisted Issue with generated ID.
        """
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        logger.info("Created issue: %s (department: %s)", issue.id, issue.department)
        return issue

    def update(self, issue: Issue) -> Issue:
        """
        Update an existing issue record.

        Args:
            issue: The modified Issue ORM instance.

        Returns:
            The updated Issue object.
        """
        self.db.commit()
        self.db.refresh(issue)
        logger.info("Updated issue: %s", issue.id)
        return issue

    def delete(self, issue: Issue) -> None:
        """
        Delete an issue record.

        Args:
            issue: The Issue ORM instance to delete.
        """
        self.db.delete(issue)
        self.db.commit()
        logger.info("Deleted issue: %s", issue.id)

    def count_by_status(self) -> List[Tuple[str, int]]:
        """
        Count issues grouped by status.

        Returns:
            List of (status, count) tuples.
        """
        from sqlalchemy import func
        return (
            self.db.query(Issue.status, func.count(Issue.id))
            .group_by(Issue.status)
            .all()
        )

    def count_by_department(self) -> List[Tuple[str, int]]:
        """
        Count issues grouped by department.

        Returns:
            List of (department, count) tuples.
        """
        from sqlalchemy import func
        return (
            self.db.query(Issue.department, func.count(Issue.id))
            .group_by(Issue.department)
            .all()
        )

    def total_count(self) -> int:
        """
        Get total number of issues.

        Returns:
            Integer count of all issues.
        """
        return self.db.query(Issue).count()

    def count_overdue(self) -> int:
        """
        Count issues that are past their SLA deadline and not closed.

        Returns:
            Integer count of overdue issues.
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return self.db.query(Issue).filter(
            Issue.sla_deadline < now,
            Issue.status != IssueStatus.CLOSED
        ).count()

