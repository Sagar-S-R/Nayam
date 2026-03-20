"""
NAYAM (नयम्) — Event Repository.

Database operations for the Event / Schedule model.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.event import Event, EventType, EventStatus

logger = logging.getLogger(__name__)


class EventRepository:
    """Repository for Event CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, event_id: UUID) -> Optional[Event]:
        return self.db.query(Event).filter(Event.id == event_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[EventStatus] = None,
        event_type: Optional[EventType] = None,
        department: Optional[str] = None,
        start_after: Optional[datetime] = None,
        start_before: Optional[datetime] = None,
    ) -> Tuple[List[Event], int]:
        query = self.db.query(Event)

        if status:
            query = query.filter(Event.status == status)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if department:
            query = query.filter(Event.department == department)
        if start_after:
            query = query.filter(Event.start_time >= start_after)
        if start_before:
            query = query.filter(Event.start_time <= start_before)

        total = query.count()
        events = query.order_by(Event.start_time.asc()).offset(skip).limit(limit).all()
        return events, total

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        logger.info("Created event: %s — %s", event.id, event.title)
        return event

    def update(self, event: Event) -> Event:
        self.db.commit()
        self.db.refresh(event)
        logger.info("Updated event: %s", event.id)
        return event

    def delete(self, event: Event) -> None:
        self.db.delete(event)
        self.db.commit()
        logger.info("Deleted event: %s", event.id)

    def total_count(self) -> int:
        return self.db.query(Event).count()

    def upcoming(self, limit: int = 10) -> List[Event]:
        """Return next N scheduled events."""
        return (
            self.db.query(Event)
            .filter(Event.status == EventStatus.SCHEDULED)
            .order_by(Event.start_time.asc())
            .limit(limit)
            .all()
        )
