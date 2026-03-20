"""
NAYAM (नयम्) — Dashboard Pydantic Schemas.

Response models for the dashboard aggregation API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DepartmentCount(BaseModel):
    """Issues count for a single department."""
    department: str
    count: int


class StatusCount(BaseModel):
    """Issues count for a single status."""
    status: str
    count: int


class RecentDocument(BaseModel):
    """Minimal document info for dashboard display."""
    id: UUID
    title: str
    uploaded_by: Optional[UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    """Aggregated dashboard data response."""
    total_issues: int
    overdue_issues: int
    issues_by_department: list[DepartmentCount]
    issues_by_status: list[StatusCount]
    total_documents: int
    recent_documents: list[RecentDocument]
