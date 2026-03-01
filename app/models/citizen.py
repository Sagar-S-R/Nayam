"""
NAYAM (नयम्) — Citizen ORM Model.

Defines the Citizen table for tracking individuals
served by public administrators.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Index, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class Citizen(Base):
    """
    Citizen ORM model.

    Attributes:
        id: UUID primary key.
        name: Full name of the citizen.
        contact_number: Phone number or contact info.
        ward: Administrative ward/region.
        created_at: Timestamp of record creation.
    """

    __tablename__ = "citizens"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    contact_number = Column(String(20), nullable=False)
    ward = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    issues = relationship(
        "Issue",
        back_populates="citizen",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_citizens_ward", "ward"),
        Index("ix_citizens_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Citizen(id={self.id}, name={self.name}, ward={self.ward})>"
