"""
NAYAM (नयम्) — Draft Pydantic Schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.draft import DraftType, DraftStatus


# ── Request ──────────────────────────────────────────────────────────
class DraftGenerateRequest(BaseModel):
    """Request to generate a new draft using AI."""
    draft_type: DraftType = Field(..., description="Template type")
    topic: str = Field(..., min_length=5, max_length=2000, description="Subject / context for the draft")
    tone: str = Field(default="Formal", max_length=100)
    audience: str = Field(default="General Public", max_length=300)
    department: Optional[str] = Field("", max_length=255)
    additional_context: Optional[str] = Field("", max_length=5000, description="Extra instructions or reference material")


class DraftUpdateRequest(BaseModel):
    """Update an existing draft. All fields optional."""
    title: Optional[str] = Field(None, min_length=2, max_length=500)
    content: Optional[str] = Field(None, max_length=50000)
    status: Optional[DraftStatus] = None
    tone: Optional[str] = None
    audience: Optional[str] = None
    department: Optional[str] = None


# ── Response ─────────────────────────────────────────────────────────
class DraftResponse(BaseModel):
    """Single draft response."""
    id: UUID
    title: str
    draft_type: DraftType
    status: DraftStatus
    content: str
    prompt_context: Optional[str]
    tone: Optional[str]
    audience: Optional[str]
    department: Optional[str]
    version: int
    extra_metadata: Optional[Dict[str, Any]]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DraftListResponse(BaseModel):
    """Paginated list of drafts."""
    total: int
    drafts: List[DraftResponse]
