"""
NAYAM (नयम्) — Issue Service.

Business logic for issue management with FK integrity checks.
"""

import logging
from typing import List, Tuple, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.issue import Issue, IssueStatus, IssuePriority
from app.repositories.citizen import CitizenRepository
from app.repositories.issue import IssueRepository
from app.schemas.issue import IssueCreateRequest, IssueUpdateRequest

logger = logging.getLogger(__name__)


class IssueService:
    """
    Service layer for issue operations.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.repo = IssueRepository(db)
        self.citizen_repo = CitizenRepository(db)

    def create_issue(self, payload: IssueCreateRequest) -> Issue:
        """
        Create a new issue with FK integrity validation.

        Args:
            payload: Issue creation data.

        Returns:
            The created Issue object.

        Raises:
            HTTPException: 404 if referenced citizen does not exist.
        """
        # Validate citizen exists (FK integrity check)
        citizen = self.citizen_repo.get_by_id(payload.citizen_id)
        if citizen is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Citizen with id {payload.citizen_id} not found.",
            )

        issue = Issue(
            citizen_id=payload.citizen_id,
            department=payload.department,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
        )
        return self.repo.create(issue)

    def get_issue(self, issue_id: UUID) -> Issue:
        """
        Retrieve a single issue by ID.

        Args:
            issue_id: UUID of the issue.

        Returns:
            The Issue object.

        Raises:
            HTTPException: 404 if issue not found.
        """
        issue = self.repo.get_by_id(issue_id)
        if issue is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with id {issue_id} not found.",
            )
        return issue

    def list_issues(
        self,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[IssueStatus] = None,
        priority: Optional[IssuePriority] = None,
        department: Optional[str] = None,
        citizen_id: Optional[UUID] = None,
        ward: Optional[str] = None,
    ) -> Tuple[List[Issue], int]:
        """
        List issues with optional filtering and pagination.

        Args:
            skip: Records to skip.
            limit: Max records.
            status_filter: Optional status filter.
            priority: Optional priority filter.
            department: Optional department filter.
            citizen_id: Optional citizen FK filter.
            ward: Optional ward filter (joins through citizen).

        Returns:
            Tuple of (issues list, total count).
        """
        return self.repo.get_all(
            skip=skip,
            limit=limit,
            status=status_filter,
            priority=priority,
            department=department,
            citizen_id=citizen_id,
            ward=ward,
        )

    def update_issue(self, issue_id: UUID, payload: IssueUpdateRequest) -> Issue:
        """
        Update an existing issue.

        Args:
            issue_id: UUID of the issue to update.
            payload: Fields to update.

        Returns:
            The updated Issue object.

        Raises:
            HTTPException: 404 if issue not found.
        """
        issue = self.get_issue(issue_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(issue, field, value)

        return self.repo.update(issue)

    def delete_issue(self, issue_id: UUID) -> None:
        """
        Delete an issue record.

        Args:
            issue_id: UUID of the issue to delete.

        Raises:
            HTTPException: 404 if issue not found.
        """
        issue = self.get_issue(issue_id)
        self.repo.delete(issue)
        logger.info("Issue deleted: %s", issue_id)
