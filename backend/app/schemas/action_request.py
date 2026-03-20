"""
NAYAM (नयम्) — ActionRequest Pydantic Schemas (Phase 2).

Request / response models for the Human-in-the-Loop approval workflow.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.action_request import ActionStatus


# ── Request Schemas ──────────────────────────────────────────────────
class ActionRequestCreate(BaseModel):
    """Schema for creating a new action request (proposed by an agent)."""
    session_id: UUID = Field(..., description="Conversation session that triggered this action")
    agent_name: str = Field(..., min_length=1, max_length=100, description="Agent that proposed the action")
    action_type: str = Field(..., min_length=1, max_length=200, description="Semantic action label")
    description: str = Field(..., min_length=1, max_length=5000, description="Human-readable explanation")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Full action parameters")


class ActionReviewRequest(BaseModel):
    """Schema for approving or rejecting an action request."""
    status: ActionStatus = Field(..., description="Must be 'approved' or 'rejected'")
    review_note: Optional[str] = Field(None, max_length=2000, description="Optional reviewer comment")


# ── Response Schemas ─────────────────────────────────────────────────
class ActionRequestResponse(BaseModel):
    """Single action request returned in responses."""
    id: UUID
    session_id: UUID
    agent_name: str
    action_type: str
    description: str
    payload: Dict[str, Any]
    status: ActionStatus
    requested_by: UUID
    reviewed_by: Optional[UUID]
    review_note: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ActionRequestListResponse(BaseModel):
    """Paginated list of action requests."""
    total: int
    actions: List[ActionRequestResponse]
