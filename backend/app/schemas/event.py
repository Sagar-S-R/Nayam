"""
NAYAM (नयम्) — Event / Schedule Pydantic Schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.event import EventType, EventStatus, EventPriority


# ── Request ──────────────────────────────────────────────────────────
class EventCreateRequest(BaseModel):
    """Create a new calendar event."""
    title: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = Field("", max_length=5000)
    event_type: EventType = Field(default=EventType.MEETING)
    priority: EventPriority = Field(default=EventPriority.MEDIUM)
    start_time: datetime
    end_time: datetime
    location: Optional[str] = Field("", max_length=500)
    attendees: Optional[str] = Field("", max_length=2000)
    department: Optional[str] = Field("", max_length=255)
    ward: Optional[str] = Field("", max_length=100)
    reminder_minutes: Optional[str] = Field("30")
    is_all_day: bool = False


class EventUpdateRequest(BaseModel):
    """Update an existing event. All fields optional."""
    title: Optional[str] = Field(None, min_length=2, max_length=300)
    description: Optional[str] = Field(None, max_length=5000)
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    priority: Optional[EventPriority] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    attendees: Optional[str] = None
    department: Optional[str] = None
    ward: Optional[str] = None
    reminder_minutes: Optional[str] = None
    is_all_day: Optional[bool] = None


# ── Response ─────────────────────────────────────────────────────────
class EventResponse(BaseModel):
    """Single event response."""
    id: UUID
    title: str
    description: Optional[str]
    event_type: EventType
    status: EventStatus
    priority: EventPriority
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    attendees: Optional[str]
    department: Optional[str]
    ward: Optional[str]
    reminder_minutes: Optional[str]
    is_all_day: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    """Paginated list of events."""
    total: int
    events: List[EventResponse]
