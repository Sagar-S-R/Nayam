"""
NAYAM (नयम्) — Schedule / Calendar API Routes.

CRUD endpoints for event management.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventListResponse,
)
from app.schemas.user import MessageResponse
from app.services.schedule import ScheduleService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=EventListResponse, summary="List events")
def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    start_after: Optional[datetime] = Query(None),
    start_before: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventListResponse:
    """Get paginated list of events with optional filters."""
    service = ScheduleService(db)
    return service.list_events(
        skip=skip,
        limit=limit,
        status=status,
        event_type=event_type,
        department=department,
        start_after=start_after,
        start_before=start_before,
    )


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
)
def create_event(
    payload: EventCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> EventResponse:
    """Create a new calendar event."""
    service = ScheduleService(db)
    event = service.create_event(payload, user_id=current_user.id)
    return EventResponse.model_validate(event)


@router.get("/{event_id}", response_model=EventResponse, summary="Get event by ID")
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventResponse:
    """Retrieve a single event by its UUID."""
    service = ScheduleService(db)
    event = service.get_event(event_id)
    return EventResponse.model_validate(event)


@router.patch("/{event_id}", response_model=EventResponse, summary="Update event")
def update_event(
    event_id: UUID,
    payload: EventUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> EventResponse:
    """Update an existing event."""
    service = ScheduleService(db)
    event = service.update_event(event_id, payload)
    return EventResponse.model_validate(event)


@router.delete("/{event_id}", response_model=MessageResponse, summary="Delete event")
def delete_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.STAFF])),
) -> MessageResponse:
    """Delete an event."""
    service = ScheduleService(db)
    service.delete_event(event_id)
    return MessageResponse(message="Event deleted successfully")


@router.get("/upcoming/list", response_model=EventListResponse, summary="Upcoming events")
def upcoming_events(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventListResponse:
    """Get upcoming scheduled events."""
    service = ScheduleService(db)
    events = service.upcoming_events(limit=limit)
    return EventListResponse(
        total=len(events),
        events=[EventResponse.model_validate(e) for e in events],
    )
