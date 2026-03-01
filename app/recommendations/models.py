"""
NAYAM (नयम्) — TaskRecommendation & ExecutionFeedback ORM Models (Phase 3).

TaskRecommendation: Autonomous administrative actions proposed by the
    recommendation engine (rule-based or ML-driven).  These flow through
    the Human-in-the-Loop approval pipeline before execution.

ExecutionFeedback: Tracks the outcome of executed recommendations
    so the system can learn from results (feedback loop).
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class RecommendationStatus(str, enum.Enum):
    """Lifecycle of a task recommendation."""
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class TaskRecommendation(Base):
    """
    Autonomous task recommendation.

    Attributes:
        id:              UUID primary key.
        ward:            Target ward.
        department:      Target department.
        title:           Short label for the recommendation.
        description:     Detailed explanation.
        priority_score:  Urgency metric (0.0 – 100.0).
        status:          Current lifecycle state.
        source_agent:    Agent that generated the recommendation.
        rationale:       JSON with supporting data/reasoning.
        created_at:      When proposed.
        reviewed_at:     When approved/rejected.
    """

    __tablename__ = "task_recommendations"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    ward = Column(String(100), nullable=False)
    department = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority_score = Column(Float, nullable=False, default=0.0)
    status = Column(
        Enum(RecommendationStatus, name="recommendation_status_enum", native_enum=False),
        nullable=False,
        default=RecommendationStatus.PROPOSED,
    )
    source_agent = Column(String(100), nullable=True)
    rationale = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────
    feedback = relationship(
        "ExecutionFeedback",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_task_rec_ward", "ward"),
        Index("ix_task_rec_department", "department"),
        Index("ix_task_rec_status", "status"),
        Index("ix_task_rec_priority", "priority_score"),
        Index("ix_task_rec_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<TaskRecommendation(ward={self.ward}, title={self.title!r}, "
            f"status={self.status}, priority={self.priority_score})>"
        )


class FeedbackOutcome(str, enum.Enum):
    """Possible outcomes after executing a recommendation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class ExecutionFeedback(Base):
    """
    Outcome tracking for executed recommendations.

    Attributes:
        id:                 UUID primary key.
        recommendation_id:  FK to the executed TaskRecommendation.
        outcome:            Execution result category.
        outcome_detail:     Human explanation of results.
        impact_score:       Measured effectiveness (0.0 – 100.0).
        executed_by:        UUID of the user who executed.
        executed_at:        When execution occurred.
    """

    __tablename__ = "execution_feedback"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    recommendation_id = Column(
        Uuid,
        ForeignKey("task_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    outcome = Column(
        Enum(FeedbackOutcome, name="feedback_outcome_enum", native_enum=False),
        nullable=False,
        default=FeedbackOutcome.SUCCESS,
    )
    outcome_detail = Column(Text, nullable=True)
    impact_score = Column(Float, nullable=True, default=0.0)
    executed_by = Column(Uuid, nullable=True)
    executed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    recommendation = relationship("TaskRecommendation", back_populates="feedback")

    __table_args__ = (
        Index("ix_exec_feedback_outcome", "outcome"),
        Index("ix_exec_feedback_executed_at", "executed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ExecutionFeedback(recommendation_id={self.recommendation_id}, "
            f"outcome={self.outcome}, impact={self.impact_score})>"
        )
