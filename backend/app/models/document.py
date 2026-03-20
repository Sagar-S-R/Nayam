"""
NAYAM (नयम्) — Document ORM Model.

Defines the Document table with FK to User (uploader),
file storage path, and stub fields for text extraction & summarization.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class Document(Base):
    """
    Document ORM model.

    Attributes:
        id: UUID primary key.
        title: Document title.
        uploaded_by: FK to the user who uploaded the document.
        file_path: Server-side path to the stored file.
        extracted_text: Text extracted from the document (stub).
        summary: AI-generated summary of the document (stub).
        created_at: Timestamp of upload.
    """

    __tablename__ = "documents"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    uploaded_by = Column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_path = Column(String(1024), nullable=False)
    extracted_text = Column(Text, nullable=True, default=None)
    summary = Column(Text, nullable=True, default=None)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    uploader = relationship("User", back_populates="documents", lazy="select")

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_documents_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"
