"""
NAYAM (नयम्) — Dashboard Service.

Aggregation logic for the dashboard API.
Uses optimized queries via repositories.
"""

import logging

from sqlalchemy.orm import Session

from app.repositories.document import DocumentRepository
from app.repositories.issue import IssueRepository
from app.schemas.dashboard import (
    DashboardResponse,
    DepartmentCount,
    StatusCount,
    RecentDocument,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service layer for dashboard aggregation.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.issue_repo = IssueRepository(db)
        self.document_repo = DocumentRepository(db)

    def get_dashboard(self) -> DashboardResponse:
        """
        Gather aggregated data for the admin dashboard.

        Performs optimized grouped queries to minimize DB round trips:
        - Total issues count
        - Issues grouped by department
        - Issues grouped by status
        - Total documents count
        - Recent documents (last 5)

        Returns:
            DashboardResponse with all aggregated data.
        """
        # Total issues (single COUNT query)
        total_issues = self.issue_repo.total_count()

        # Issues by department (GROUP BY query)
        dept_counts = self.issue_repo.count_by_department()
        issues_by_department = [
            DepartmentCount(department=dept, count=count)
            for dept, count in dept_counts
        ]

        # Issues by status (GROUP BY query)
        status_counts = self.issue_repo.count_by_status()
        issues_by_status = [
            StatusCount(status=s.value if hasattr(s, "value") else str(s), count=count)
            for s, count in status_counts
        ]

        # Documents
        total_documents = self.document_repo.total_count()
        recent_docs = self.document_repo.get_recent(limit=5)
        recent_documents = [
            RecentDocument.model_validate(doc) for doc in recent_docs
        ]

        logger.info(
            "Dashboard aggregated: %d issues, %d documents",
            total_issues,
            total_documents,
        )

        return DashboardResponse(
            total_issues=total_issues,
            issues_by_department=issues_by_department,
            issues_by_status=issues_by_status,
            total_documents=total_documents,
            recent_documents=recent_documents,
        )
