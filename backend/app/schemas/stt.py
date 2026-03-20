"""
NAYAM (नयम्) — STT (Speech-to-Text) Pydantic Schemas.

Request/response models for audio transcription, content classification,
and intelligent ingestion routing.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Content Classification ───────────────────────────────────────────

class ContentCategory(str, Enum):
    """Category determined by LLM classification of transcribed text."""
    POLICY_DOCUMENT = "policy_document"      # Draft policy, circular, guideline, SOP
    CITIZEN_ISSUE = "citizen_issue"          # Complaint, grievance, service request
    MEETING_MINUTES = "meeting_minutes"      # Meeting transcript, discussion notes
    FIELD_REPORT = "field_report"            # Field inspection, site visit report
    GENERAL_QUERY = "general_query"          # Question for AI agent, not data ingestion


class ClassificationResult(BaseModel):
    """Result of LLM-based content classification."""
    category: ContentCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="LLM's explanation for the classification")
    extracted_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured fields extracted: title, department, ward, priority, citizen_name, etc.",
    )


# ── Transcription Responses ──────────────────────────────────────────

class TranscribeResponse(BaseModel):
    """Response from basic transcription (audio → text only)."""
    transcript: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    provider: str = Field(..., description="STT provider used: groq_whisper, openai_whisper, bhashini, local_whisper")


class TranscribeAndClassifyResponse(BaseModel):
    """Response from transcription + classification (no ingestion)."""
    transcript: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    provider: str
    classification: ClassificationResult


class IngestResult(BaseModel):
    """What was created as a result of ingestion."""
    category: ContentCategory
    created_type: str = Field(..., description="'document', 'issue', or 'agent_query'")
    created_id: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    detail: str = Field(..., description="Human-readable summary of what happened")


class TranscribeAndIngestResponse(BaseModel):
    """Full pipeline response: audio → text → classify → route → create."""
    transcript: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    provider: str
    classification: ClassificationResult
    ingestion: IngestResult
