"""
NAYAM (नयम्) — Embedding Repository (Phase 2).

Handles all database operations for the Embedding model.
Provides storage, retrieval by source, and in-process cosine
similarity search (to be replaced by pgvector in a future phase).
"""

import hashlib
import logging
from typing import List, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session

from app.models.embedding import Embedding

logger = logging.getLogger(__name__)


class EmbeddingRepository:
    """
    Repository for Embedding CRUD operations and similarity search.

    Args:
        db: SQLAlchemy database session.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _content_hash(text: str) -> str:
        """Return SHA-256 hex digest for a text string."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Returns:
            Float in [-1, 1]. Higher = more similar.
        """
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    # ── Single Record ────────────────────────────────────────────

    def get_by_id(self, embedding_id: UUID) -> Optional[Embedding]:
        """
        Retrieve an embedding by its UUID.

        Args:
            embedding_id: The UUID of the embedding.

        Returns:
            Embedding object or None.
        """
        return (
            self.db.query(Embedding)
            .filter(Embedding.id == embedding_id)
            .first()
        )

    def create(self, embedding: Embedding) -> Embedding:
        """
        Persist a new embedding record.

        Args:
            embedding: The Embedding ORM instance.

        Returns:
            The persisted Embedding with generated ID.
        """
        self.db.add(embedding)
        self.db.commit()
        self.db.refresh(embedding)
        logger.info(
            "Stored embedding: source_type=%s source_id=%s chunk=%d",
            embedding.source_type, embedding.source_id, embedding.chunk_index,
        )
        return embedding

    def create_many(self, embeddings: List[Embedding]) -> List[Embedding]:
        """
        Persist multiple embeddings in one transaction.

        Args:
            embeddings: List of Embedding ORM instances.

        Returns:
            The persisted embeddings.
        """
        self.db.add_all(embeddings)
        self.db.commit()
        for e in embeddings:
            self.db.refresh(e)
        logger.info("Stored %d embeddings", len(embeddings))
        return embeddings

    # ── Source Lookups ───────────────────────────────────────────

    def get_by_source(
        self,
        source_type: str,
        source_id: UUID,
    ) -> List[Embedding]:
        """
        Retrieve all embedding chunks for a specific source.

        Args:
            source_type: e.g. "conversation", "document".
            source_id: UUID of the source record.

        Returns:
            List of Embedding objects, ordered by chunk_index.
        """
        return (
            self.db.query(Embedding)
            .filter(
                Embedding.source_type == source_type,
                Embedding.source_id == source_id,
            )
            .order_by(Embedding.chunk_index)
            .all()
        )

    def exists_by_content_hash(self, content_hash: str) -> bool:
        """
        Check whether an embedding with a given content hash exists.

        Args:
            content_hash: SHA-256 hex digest.

        Returns:
            True if a record with this hash exists.
        """
        return (
            self.db.query(Embedding)
            .filter(Embedding.content_hash == content_hash)
            .count()
            > 0
        )

    # ── Similarity Search ────────────────────────────────────────

    def search_similar(
        self,
        query_embedding: List[float],
        source_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Tuple[Embedding, float]]:
        """
        Find the most similar embeddings using cosine similarity.

        This is an in-process brute-force scan; suitable for < 50 k
        records.  For production scale, migrate to pgvector.

        Args:
            query_embedding: The query vector.
            source_type: Optionally restrict to a source type.
            top_k: Number of results.

        Returns:
            List of (Embedding, score) tuples, descending by score.
        """
        query = self.db.query(Embedding)
        if source_type:
            query = query.filter(Embedding.source_type == source_type)

        all_embeddings = query.all()

        scored: List[Tuple[Embedding, float]] = []
        for emb in all_embeddings:
            score = self._cosine_similarity(query_embedding, emb.embedding)
            scored.append((emb, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ── Deletion ─────────────────────────────────────────────────

    def delete_by_source(self, source_type: str, source_id: UUID) -> int:
        """
        Delete all embeddings for a specific source.

        Args:
            source_type: e.g. "conversation", "document".
            source_id: UUID of the source record.

        Returns:
            Number of deleted rows.
        """
        count = (
            self.db.query(Embedding)
            .filter(
                Embedding.source_type == source_type,
                Embedding.source_id == source_id,
            )
            .delete(synchronize_session="fetch")
        )
        self.db.commit()
        logger.info(
            "Deleted %d embeddings for %s/%s", count, source_type, source_id,
        )
        return count

    def total_count(self) -> int:
        """
        Get total number of embedding records.

        Returns:
            Integer count.
        """
        return self.db.query(Embedding).count()
