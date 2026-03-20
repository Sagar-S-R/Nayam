"""
NAYAM (नयम्) — Notification Schemas.

Lightweight aggregation response for the notification bell.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NotificationItem(BaseModel):
    """A single notification entry."""

    id: str = Field(..., description="Unique key for dedup / dismiss")
    type: str = Field(
        ...,
        description="Category: 'critical_issue', 'pending_approval', 'new_document', 'system'",
    )
    title: str
    detail: str
    severity: str = Field(default="info", description="info | warning | critical")
    timestamp: datetime
    link: Optional[str] = Field(
        default=None,
        description="Frontend route to navigate on click",
    )


class NotificationsResponse(BaseModel):
    """Aggregated notification payload."""

    total: int = Field(..., description="Total unread / active count")
    items: List[NotificationItem]
