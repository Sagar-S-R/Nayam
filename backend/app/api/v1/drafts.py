"""
NAYAM (नयम्) — Draft Generation API Routes.

Endpoints for AI-powered draft generation and management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.draft import (
    DraftGenerateRequest,
    DraftUpdateRequest,
    DraftResponse,
    DraftListResponse,
)
from app.schemas.user import MessageResponse
from app.services.draft import DraftService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=DraftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new draft using AI",
)
def generate_draft(
    payload: DraftGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> DraftResponse:
    """Generate a new speech, letter, or official document using AI."""
    service = DraftService(db)
    draft = service.generate_draft(payload, user_id=current_user.id)
    return DraftResponse.model_validate(draft)


@router.get("/", response_model=DraftListResponse, summary="List drafts")
def list_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    draft_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftListResponse:
    """Get paginated list of drafts with optional filters."""
    service = DraftService(db)
    return service.list_drafts(
        skip=skip,
        limit=limit,
        draft_type=draft_type,
        status=status,
        department=department,
    )


@router.get("/{draft_id}", response_model=DraftResponse, summary="Get draft by ID")
def get_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftResponse:
    """Retrieve a single draft by its UUID."""
    service = DraftService(db)
    draft = service.get_draft(draft_id)
    return DraftResponse.model_validate(draft)


@router.patch("/{draft_id}", response_model=DraftResponse, summary="Update draft")
def update_draft(
    draft_id: UUID,
    payload: DraftUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> DraftResponse:
    """Update an existing draft's content, status, or metadata."""
    service = DraftService(db)
    draft = service.update_draft(draft_id, payload)
    return DraftResponse.model_validate(draft)


@router.delete("/{draft_id}", response_model=MessageResponse, summary="Delete draft")
def delete_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> MessageResponse:
    """Delete a draft."""
    service = DraftService(db)
    service.delete_draft(draft_id)
    return MessageResponse(message="Draft deleted successfully")
