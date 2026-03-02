"""
NAYAM (नयम्) — Draft ORM Model.

AI-generated speeches, official responses, press releases,
and other formal documents with template support and versioning.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Enum, DateTime, Integer, ForeignKey, Index, Uuid
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class DraftType(str, enum.Enum):
    """Template category for the draft."""
    SPEECH = "Speech"
    OFFICIAL_RESPONSE = "Official Response"
    PRESS_RELEASE = "Press Release"
    POLICY_BRIEF = "Policy Brief"
    MEETING_AGENDA = "Meeting Agenda"
    PUBLIC_NOTICE = "Public Notice"
    LETTER = "Formal Letter"
    RTI_RESPONSE = "RTI Response"
    CIRCULAR = "Government Circular"


class DraftStatus(str, enum.Enum):
    """Lifecycle status of a draft."""
    GENERATING = "Generating"
    DRAFT = "Draft"
    UNDER_REVIEW = "Under Review"
    APPROVED = "Approved"
    PUBLISHED = "Published"


class Draft(Base):
    """
    Draft ORM model.

    Attributes:
        id: UUID primary key.
        title: Title of the draft.
        draft_type: Template category.
        status: Lifecycle state.
        content: The full generated / edited text.
        prompt_context: The original prompt / topic / context given.
        tone: Desired tone (formal, empathetic, assertive, etc.).
        audience: Target audience description.
        department: Related department.
        version: Integer version counter.
        metadata: Extra JSON metadata (word_count, language, etc.).
        created_by: FK to the user who created this draft.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "drafts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column(String(500), nullable=False)
    draft_type = Column(
        Enum(DraftType, name="draft_type_enum", native_enum=False),
        nullable=False,
        default=DraftType.SPEECH,
    )
    status = Column(
        Enum(DraftStatus, name="draft_status_enum", native_enum=False),
        nullable=False,
        default=DraftStatus.DRAFT,
    )
    content = Column(Text, nullable=False, default="")
    prompt_context = Column(Text, nullable=True, default="")
    tone = Column(String(100), nullable=True, default="Formal")
    audience = Column(String(300), nullable=True, default="General Public")
    department = Column(String(255), nullable=True, default="")
    version = Column(Integer, nullable=False, default=1)
    extra_metadata = Column(JSON, nullable=True, default=dict)

    created_by = Column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], lazy="select")

    __table_args__ = (
        Index("ix_drafts_type", "draft_type"),
        Index("ix_drafts_status", "status"),
        Index("ix_drafts_created_at", "created_at"),
        Index("ix_drafts_department", "department"),
    )

    def __repr__(self) -> str:
        return f"<Draft(id={self.id}, title={self.title}, type={self.draft_type})>"
