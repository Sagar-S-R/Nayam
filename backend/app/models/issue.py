"""
NAYAM (नयम्) — Issue ORM Model.

Defines the Issue table with FK to Citizen,
status tracking, and priority levels.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Float, String, Text, Enum, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class IssueStatus(str, enum.Enum):
    """Enumeration of issue statuses."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"


class IssuePriority(str, enum.Enum):
    """Enumeration of issue priority levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Issue(Base):
    """
    Issue ORM model.

    Attributes:
        id: UUID primary key.
        citizen_id: FK to the citizen who raised the issue.
        department: Department the issue is assigned to.
        description: Detailed description of the issue.
        status: Current status (Open, In Progress, Closed).
        priority: Priority level (Low, Medium, High).
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "issues"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    citizen_id = Column(
        Uuid,
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        Enum(IssueStatus, name="issue_status_enum", native_enum=False),
        nullable=False,
        default=IssueStatus.OPEN,
    )
    priority = Column(
        Enum(IssuePriority, name="issue_priority_enum", native_enum=False),
        nullable=False,
        default=IssuePriority.MEDIUM,
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

    # ── SLA Tracking ─────────────────────────────────────────────
    sla_deadline = Column(DateTime(timezone=True), nullable=True)

    # ── Geo Metadata (Phase 2) ───────────────────────────────────
    latitude = Column(Float, nullable=True, default=None)
    longitude = Column(Float, nullable=True, default=None)
    location_description = Column(String(500), nullable=True, default=None)

    # ── Relationships ────────────────────────────────────────────
    citizen = relationship("Citizen", back_populates="issues", lazy="select")

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_issues_department", "department"),
        Index("ix_issues_status", "status"),
        Index("ix_issues_priority", "priority"),
        Index("ix_issues_created_at", "created_at"),
        Index("ix_issues_geo", "latitude", "longitude"),
        Index("ix_issues_sla", "sla_deadline"),
    )

    def __repr__(self) -> str:
        return f"<Issue(id={self.id}, department={self.department}, status={self.status})>"
