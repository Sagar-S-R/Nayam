"""
NAYAM (नयम्) — Schedule / Event Service.

Business logic for calendar events.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import Event, EventType, EventStatus, EventPriority
from app.repositories.event import EventRepository
from app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventListResponse,
)

logger = logging.getLogger(__name__)


class ScheduleService:
    """Service layer for schedule management."""

    def __init__(self, db: Session) -> None:
        self.repo = EventRepository(db)

    def list_events(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        event_type: Optional[str] = None,
        department: Optional[str] = None,
        start_after: Optional[datetime] = None,
        start_before: Optional[datetime] = None,
    ) -> EventListResponse:
        status_enum = EventStatus(status) if status else None
        type_enum = EventType(event_type) if event_type else None
        events, total = self.repo.get_all(
            skip=skip,
            limit=limit,
            status=status_enum,
            event_type=type_enum,
            department=department,
            start_after=start_after,
            start_before=start_before,
        )
        return EventListResponse(
            total=total,
            events=[EventResponse.model_validate(e) for e in events],
        )

    def get_event(self, event_id: UUID) -> Event:
        event = self.repo.get_by_id(event_id)
        if not event:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event

    def create_event(self, payload: EventCreateRequest, user_id: Optional[UUID] = None) -> Event:
        event = Event(
            title=payload.title,
            description=payload.description or "",
            event_type=payload.event_type,
            status=EventStatus.SCHEDULED,
            priority=payload.priority,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location or "",
            attendees=payload.attendees or "",
            department=payload.department or "",
            ward=payload.ward or "",
            reminder_minutes=payload.reminder_minutes or "30",
            is_all_day=payload.is_all_day,
            created_by=user_id,
        )
        return self.repo.create(event)

    def update_event(self, event_id: UUID, payload: EventUpdateRequest) -> Event:
        event = self.get_event(event_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        return self.repo.update(event)

    def delete_event(self, event_id: UUID) -> None:
        event = self.get_event(event_id)
        self.repo.delete(event)

    def upcoming_events(self, limit: int = 10) -> list[Event]:
        return self.repo.upcoming(limit=limit)
