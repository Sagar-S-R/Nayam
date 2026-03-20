"""
NAYAM (नयम्) — Citizens API Routes.

CRUD endpoints for citizen management.
All business logic delegated to CitizenService.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.mcd_wards import get_valid_wards
from app.models.user import User, UserRole
from app.schemas.citizen import (
    CitizenCreateRequest,
    CitizenUpdateRequest,
    CitizenResponse,
    CitizenListResponse,
)
from app.schemas.user import MessageResponse
from app.services.citizen import CitizenService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/wards",
    response_model=dict,
    summary="Get list of valid MCD wards",
)
def get_wards(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get list of valid MCD wards for dropdown selection.
    
    Returns:
        Dict with 'wards' list.
    """
    return {"wards": get_valid_wards()}


@router.post(
    "/",
    response_model=CitizenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new citizen",
)
def create_citizen(
    payload: CitizenCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> CitizenResponse:
    """
    Create a new citizen record.

    Requires: Leader or Staff role.
    """
    service = CitizenService(db)
    citizen = service.create_citizen(payload)
    return CitizenResponse.model_validate(citizen)


@router.get(
    "/",
    response_model=CitizenListResponse,
    summary="List all citizens",
)
def list_citizens(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    ward: Optional[str] = Query(None, description="Filter by ward"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CitizenListResponse:
    """
    List citizens with optional filtering and pagination.

    Requires: Any authenticated user.
    """
    service = CitizenService(db)
    citizens, total = service.list_citizens(skip=skip, limit=limit, ward=ward, search=search)
    return CitizenListResponse(
        total=total,
        citizens=[CitizenResponse.model_validate(c) for c in citizens],
    )


@router.get(
    "/{citizen_id}",
    response_model=CitizenResponse,
    summary="Get citizen by ID",
)
def get_citizen(
    citizen_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CitizenResponse:
    """
    Retrieve a single citizen by UUID.

    Requires: Any authenticated user.
    """
    service = CitizenService(db)
    citizen = service.get_citizen(citizen_id)
    return CitizenResponse.model_validate(citizen)


@router.put(
    "/{citizen_id}",
    response_model=CitizenResponse,
    summary="Update citizen",
)
def update_citizen(
    citizen_id: UUID,
    payload: CitizenUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> CitizenResponse:
    """
    Update an existing citizen record.

    Requires: Leader or Staff role.
    """
    service = CitizenService(db)
    citizen = service.update_citizen(citizen_id, payload)
    return CitizenResponse.model_validate(citizen)


@router.delete(
    "/{citizen_id}",
    response_model=MessageResponse,
    summary="Delete citizen",
)
def delete_citizen(
    citizen_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER])),
) -> MessageResponse:
    """
    Delete a citizen record.

    Requires: Leader role only.
    """
    service = CitizenService(db)
    service.delete_citizen(citizen_id)
    return MessageResponse(message="Citizen deleted successfully.")
