"""
NAYAM (नयम्) — Agent Pydantic Schemas (Phase 2).

Request / response models for the multi-agent query system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────
class AgentQueryRequest(BaseModel):
    """Schema for submitting a query to the agent system."""
    query: str = Field(..., min_length=1, max_length=5000, description="Natural-language question or command")
    session_id: Optional[str] = Field(None, description="Existing session ID or None to create new")
    agent_name: Optional[str] = Field(None, description="Force a specific agent (bypasses router)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extra context hints")


# ── Response Schemas ─────────────────────────────────────────────────
class PendingActionSummary(BaseModel):
    """Compact summary of a pending action created by an agent."""
    id: UUID
    action_type: str
    description: str
    status: str


class AgentQueryResponse(BaseModel):
    """Response from the agent query pipeline."""
    session_id: str
    agent_name: str
    response: str
    confidence: float
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    pending_actions: List[PendingActionSummary] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    """Agent descriptor returned in listings."""
    name: str
    description: str


class AgentListResponse(BaseModel):
    """List of available agents."""
    agents: List[AgentInfo]


class SessionHistoryMessage(BaseModel):
    """A single message within session history."""
    role: str
    content: str
    agent_name: Optional[str] = None
    created_at: Optional[str] = None


class SessionHistoryResponse(BaseModel):
    """Full conversation history for a session."""
    session_id: str
    total: int
    messages: List[SessionHistoryMessage]
