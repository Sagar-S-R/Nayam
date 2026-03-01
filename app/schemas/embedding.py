"""
NAYAM (नयम्) — Embedding Pydantic Schemas (Phase 2).

Request / response models for the vector embedding storage.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────
class EmbeddingCreateRequest(BaseModel):
    """Schema for storing a new embedding record."""
    source_type: str = Field(..., min_length=1, max_length=50, description="e.g. conversation, document")
    source_id: UUID = Field(..., description="UUID of the source record")
    chunk_index: int = Field(default=0, ge=0, description="Chunk order within source")
    chunk_text: str = Field(..., min_length=1, description="Original text that was embedded")
    embedding: List[float] = Field(..., description="Vector as list of floats")
    model_name: str = Field(default="text-embedding-3-small", max_length=100)


class EmbeddingSearchRequest(BaseModel):
    """Schema for a nearest-neighbour search against stored embeddings."""
    query_embedding: List[float] = Field(..., description="Query vector")
    source_type: Optional[str] = Field(None, description="Optionally filter by source type")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")


# ── Response Schemas ─────────────────────────────────────────────────
class EmbeddingResponse(BaseModel):
    """Single embedding record returned in responses."""
    id: UUID
    source_type: str
    source_id: UUID
    chunk_index: int
    chunk_text: str
    dimensions: int
    model_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EmbeddingSearchResult(BaseModel):
    """A single search result with similarity score."""
    embedding_id: UUID
    source_type: str
    source_id: UUID
    chunk_text: str
    score: float = Field(..., description="Cosine similarity score")


class EmbeddingSearchResponse(BaseModel):
    """Collection of search results."""
    query_source_type: Optional[str]
    top_k: int
    results: List[EmbeddingSearchResult]
