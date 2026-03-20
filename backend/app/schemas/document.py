"""
NAYAM (नयम्) — Document Pydantic Schemas.

Request/response models for document upload and management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Schema for document data in responses."""
    id: UUID
    title: str
    uploaded_by: Optional[UUID]
    file_path: str
    extracted_text: Optional[str]
    summary: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema for paginated document list."""
    total: int
    documents: list[DocumentUploadResponse]


class DocumentSummaryResponse(BaseModel):
    """Schema for document with extracted text and summary."""
    id: UUID
    title: str
    extracted_text: Optional[str]
    summary: Optional[str]
