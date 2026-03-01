"""
NAYAM (नयम्) — Embedding ORM Model (Phase 2).

Stores vector embeddings for conversations and documents,
enabling semantic retrieval (RAG) and context memory.

The embedding vector is stored as a JSON-serialised list of floats.
This avoids a hard dependency on pgvector for Phase 2 foundations
while remaining easy to migrate later.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer, Index, Uuid
from sqlalchemy.types import JSON

from app.core.database import Base


class Embedding(Base):
    """
    Embedding ORM model.

    Attributes:
        id: UUID primary key.
        source_type: Origin kind — "conversation", "document", etc.
        source_id: UUID of the source record.
        content_hash: SHA-256 of the original text (dedup guard).
        chunk_index: Order of the chunk within a source (0-based).
        chunk_text: The raw text that was embedded.
        embedding: JSON list of floats (vector).
        dimensions: Length of the embedding vector.
        model_name: Name of the embedding model used.
        created_at: Timestamp of creation.
    """

    __tablename__ = "embeddings"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    source_type = Column(String(50), nullable=False)
    source_id = Column(Uuid, nullable=False)
    content_hash = Column(String(64), nullable=False)
    chunk_index = Column(Integer, nullable=False, default=0)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)
    dimensions = Column(Integer, nullable=False)
    model_name = Column(String(100), nullable=False, default="text-embedding-3-small")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_embeddings_source", "source_type", "source_id"),
        Index("ix_embeddings_content_hash", "content_hash"),
        Index("ix_embeddings_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Embedding(id={self.id}, source_type={self.source_type}, "
            f"source_id={self.source_id}, dim={self.dimensions})>"
        )
