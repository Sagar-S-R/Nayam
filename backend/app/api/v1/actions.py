"""
NAYAM (नयम्) — Action Approval API Routes (Phase 2).

Endpoints for listing, inspecting, and reviewing (approve/reject)
agent-proposed action requests.  Enforces RBAC via deps.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.action_request import ActionStatus
from app.models.user import User, UserRole
from app.schemas.action_request import (
    ActionReviewRequest,
    ActionRequestResponse,
    ActionRequestListResponse,
)
from app.schemas.user import MessageResponse
from app.services.approval import ApprovalService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=ActionRequestListResponse,
    summary="List action requests",
)
def list_actions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[ActionStatus] = Query(None, alias="status", description="Filter by status"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionRequestListResponse:
    """
    List action requests with optional filters and pagination.

    Requires: Any authenticated user.
    """
    service = ApprovalService(db)
    actions, total = service.list_all(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        agent_name=agent_name,
    )
    return ActionRequestListResponse(
        total=total,
        actions=[ActionRequestResponse.model_validate(a) for a in actions],
    )


@router.get(
    "/pending",
    response_model=ActionRequestListResponse,
    summary="List pending action requests",
)
def list_pending_actions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionRequestListResponse:
    """
    List only pending (un-reviewed) action requests.

    Requires: Any authenticated user.
    """
    service = ApprovalService(db)
    actions, total = service.list_pending(skip=skip, limit=limit)
    return ActionRequestListResponse(
        total=total,
        actions=[ActionRequestResponse.model_validate(a) for a in actions],
    )


@router.get(
    "/{action_id}",
    response_model=ActionRequestResponse,
    summary="Get action request details",
)
def get_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionRequestResponse:
    """
    Retrieve a single action request by ID.

    Requires: Any authenticated user.
    """
    service = ApprovalService(db)
    action = service.get_action(action_id)
    return ActionRequestResponse.model_validate(action)


@router.post(
    "/{action_id}/review",
    response_model=ActionRequestResponse,
    summary="Approve or reject an action request",
)
def review_action(
    action_id: UUID,
    payload: ActionReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> ActionRequestResponse:
    """
    Approve or reject a pending action request.

    Requires: Leader or Staff role.
    """
    service = ApprovalService(db)
    if payload.status == ActionStatus.APPROVED:
        action = service.approve(action_id, current_user, payload.review_note)
    elif payload.status == ActionStatus.REJECTED:
        action = service.reject(action_id, current_user, payload.review_note)
    else:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review status must be 'approved' or 'rejected'.",
        )
    return ActionRequestResponse.model_validate(action)
