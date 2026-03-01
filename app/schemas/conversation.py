"""
NAYAM (नयम्) — Conversation Pydantic Schemas (Phase 2).

Request / response models for the conversation memory subsystem.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.conversation import MessageRole


# ── Request Schemas ──────────────────────────────────────────────────
class ConversationMessageCreate(BaseModel):
    """Schema for appending a single message to a conversation session."""
    session_id: UUID = Field(..., description="Conversation session UUID")
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., min_length=1, max_length=10000, description="Message text")
    agent_name: Optional[str] = Field(None, max_length=100, description="Agent that handled this turn")


# ── Response Schemas ─────────────────────────────────────────────────
class ConversationMessageResponse(BaseModel):
    """Single conversation turn returned in responses."""
    id: UUID
    session_id: UUID
    user_id: UUID
    role: MessageRole
    content: str
    agent_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationHistoryResponse(BaseModel):
    """Full conversation session history."""
    session_id: UUID
    total: int
    messages: List[ConversationMessageResponse]
