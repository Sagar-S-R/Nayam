"""
NAYAM (नयम्) — Issues API Routes.

CRUD endpoints with filtering for issue management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.issue import IssueStatus, IssuePriority
from app.models.user import User, UserRole
from app.schemas.issue import (
    IssueCreateRequest,
    IssueUpdateRequest,
    IssueResponse,
    IssueListResponse,
)
from app.schemas.user import MessageResponse
from app.services.issue import IssueService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new issue",
)
def create_issue(
    payload: IssueCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> IssueResponse:
    """
    Create a new issue linked to a citizen.

    Requires: Leader or Staff role.
    """
    service = IssueService(db)
    issue = service.create_issue(payload)
    return IssueResponse.model_validate(issue)


@router.get(
    "/",
    response_model=IssueListResponse,
    summary="List issues with filters",
)
def list_issues(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status_filter: Optional[IssueStatus] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[IssuePriority] = Query(None, description="Filter by priority"),
    department: Optional[str] = Query(None, description="Filter by department"),
    citizen_id: Optional[UUID] = Query(None, description="Filter by citizen"),
    ward: Optional[str] = Query(None, description="Filter by citizen ward"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IssueListResponse:
    """
    List issues with optional filtering and pagination.

    Requires: Any authenticated user.
    """
    service = IssueService(db)
    issues, total = service.list_issues(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        priority=priority,
        department=department,
        citizen_id=citizen_id,
        ward=ward,
    )
    return IssueListResponse(
        total=total,
        issues=[IssueResponse.model_validate(i) for i in issues],
    )


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Get issue by ID",
)
def get_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IssueResponse:
    """
    Retrieve a single issue by UUID.

    Requires: Any authenticated user.
    """
    service = IssueService(db)
    issue = service.get_issue(issue_id)
    return IssueResponse.model_validate(issue)


@router.put(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Update issue",
)
def update_issue(
    issue_id: UUID,
    payload: IssueUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> IssueResponse:
    """
    Update an existing issue.

    Requires: Leader or Staff role.
    """
    service = IssueService(db)
    issue = service.update_issue(issue_id, payload)
    return IssueResponse.model_validate(issue)


@router.delete(
    "/{issue_id}",
    response_model=MessageResponse,
    summary="Delete issue",
)
def delete_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> MessageResponse:
    """
    Delete an issue record.

    Requires: Leader role only.
    """
    service = IssueService(db)
    service.delete_issue(issue_id)
    return MessageResponse(message="Issue deleted successfully.")
