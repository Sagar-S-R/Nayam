"""
NAYAM (नयम्) — Schedule / Event ORM Model.

Implements calendar events for leaders & administrators:
meetings, hearings, site visits, deadlines, and reminders.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Enum, DateTime, Boolean, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventType(str, enum.Enum):
    """Type of calendar event."""
    MEETING = "Meeting"
    HEARING = "Hearing"
    SITE_VISIT = "Site Visit"
    DEADLINE = "Deadline"
    REVIEW = "Review"
    PUBLIC_EVENT = "Public Event"
    OTHER = "Other"


class EventStatus(str, enum.Enum):
    """Lifecycle status of an event."""
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class EventPriority(str, enum.Enum):
    """Priority level for an event."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Event(Base):
    """
    Event / Schedule ORM model.

    Attributes:
        id: UUID primary key.
        title: Short event title.
        description: Detailed event description / agenda.
        event_type: Category of the event.
        status: Current lifecycle state.
        priority: Importance level.
        start_time: When the event starts.
        end_time: When the event ends.
        location: Physical or virtual location.
        attendees: Comma-separated list of attendee names.
        department: Related department.
        ward: Related ward (optional).
        reminder_minutes: Minutes before event to send reminder.
        is_all_day: Whether the event spans the full day.
        created_by: FK to the user who created this event.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "events"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True, default="")
    event_type = Column(
        Enum(EventType, name="event_type_enum", native_enum=False),
        nullable=False,
        default=EventType.MEETING,
    )
    status = Column(
        Enum(EventStatus, name="event_status_enum", native_enum=False),
        nullable=False,
        default=EventStatus.SCHEDULED,
    )
    priority = Column(
        Enum(EventPriority, name="event_priority_enum", native_enum=False),
        nullable=False,
        default=EventPriority.MEDIUM,
    )
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(500), nullable=True, default="")
    attendees = Column(Text, nullable=True, default="")
    department = Column(String(255), nullable=True, default="")
    ward = Column(String(100), nullable=True, default="")
    reminder_minutes = Column(String(10), nullable=True, default="30")
    is_all_day = Column(Boolean, nullable=False, default=False)

    created_by = Column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], lazy="select")

    __table_args__ = (
        Index("ix_events_start_time", "start_time"),
        Index("ix_events_status", "status"),
        Index("ix_events_type", "event_type"),
        Index("ix_events_department", "department"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, start={self.start_time})>"
