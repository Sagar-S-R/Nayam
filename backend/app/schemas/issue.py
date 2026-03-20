"""
NAYAM (नयम्) — Issue Pydantic Schemas.

Request/response models for issue management with filtering support.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, field_validator

from app.core.security_utils import sanitize_text

from app.models.issue import IssueStatus, IssuePriority


# ── Request Schemas ──────────────────────────────────────────────────
class IssueCreateRequest(BaseModel):
    """Schema for creating a new issue."""
    citizen_id: UUID = Field(..., description="UUID of the citizen raising the issue")
    department: str = Field(..., min_length=2, max_length=255, description="Department name")
    description: str = Field(..., min_length=10, max_length=5000, description="Issue description")
    status: IssueStatus = Field(default=IssueStatus.OPEN, description="Initial status")
    priority: IssuePriority = Field(default=IssuePriority.MEDIUM, description="Priority level")
    # Phase 2 — Geo metadata (optional)
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    location_description: Optional[str] = Field(None, max_length=500, description="Free-text location note")

    @field_validator("department", "description", "location_description", mode="before")
    @classmethod
    def sanitize_inputs(cls, v):
        return sanitize_text(v) if isinstance(v, str) else v


class IssueUpdateRequest(BaseModel):
    """Schema for updating an existing issue. All fields optional."""
    department: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    # Phase 2 — Geo metadata (optional)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_description: Optional[str] = Field(None, max_length=500)

    @field_validator("department", "description", "location_description", mode="before")
    @classmethod
    def sanitize_inputs(cls, v):
        return sanitize_text(v) if isinstance(v, str) else v


# ── Response Schemas ─────────────────────────────────────────────────
class IssueResponse(BaseModel):
    """Schema for issue data in responses."""
    id: UUID
    citizen_id: UUID
    department: str
    description: str
    status: IssueStatus
    priority: IssuePriority
    sla_deadline: Optional[datetime]
    latitude: Optional[float]
    longitude: Optional[float]
    location_description: Optional[str]
    created_at: datetime
    updated_at: datetime

    @computed_field
    def is_overdue(self) -> bool:
        if not self.sla_deadline:
            return False
        if self.status == IssueStatus.CLOSED:
            return False
        
        # Make sure we compare aware datetimes
        now = datetime.now(timezone.utc)
        # If sla_deadline is naive (e.g. from sqlite testing), make it aware
        if self.sla_deadline.tzinfo is None:
            deadline = self.sla_deadline.replace(tzinfo=timezone.utc)
        else:
            deadline = self.sla_deadline
            
        return now > deadline

    model_config = {"from_attributes": True}


class IssueListResponse(BaseModel):
    """Schema for paginated issue list."""
    total: int
    issues: list[IssueResponse]
