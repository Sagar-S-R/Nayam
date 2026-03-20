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


class SourceCitationSchema(BaseModel):
    """Minimal schema for source citations in API responses."""
    document_title: str = Field(..., description="Title of the source document")
    chunk_preview: str = Field(..., description="30-40 word preview of the chunk")
    document_id: Optional[UUID] = Field(None, description="UUID of the source document")
    chunk_index: Optional[int] = Field(None, description="Index of the chunk in the document")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Cosine similarity score (0.0-1.0)")


class SourceCitationResponse(BaseModel):
    """Citation of a source document used in RAG retrieval."""
    document_id: UUID
    document_title: str
    chunk_index: int
    chunk_preview: str = Field(..., description="30-40 word preview of the chunk")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")


class AgentQueryResponse(BaseModel):
    """Response from the agent query pipeline."""
    response: str
    agent_name: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")
    sources: List[SourceCitationSchema] = Field(default_factory=list, description="Source documents cited in response")
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
