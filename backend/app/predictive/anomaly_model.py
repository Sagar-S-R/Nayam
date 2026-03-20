"""
NAYAM (नयम्) — AnomalyLog ORM Model (Phase 3).

Records anomalous spikes in issue frequency detected by the
Predictive Governance Engine.  Each entry represents a single
anomaly event with its statistical context.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Float, Index, Integer, String, Text, Uuid,
)

from app.core.database import Base


class AnomalySeverity(str, enum.Enum):
    """Anomaly severity level."""
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class AnomalyLog(Base):
    """
    Anomaly detection event log.

    Attributes:
        id:                UUID primary key.
        ward:              Ward where the anomaly was detected.
        department:        Department context.
        anomaly_type:      Label, e.g. "spike", "drop", "pattern_shift".
        severity:          WARNING / ALERT / CRITICAL.
        expected_value:    Baseline value the model predicted.
        actual_value:      Observed value that triggered the anomaly.
        deviation_percent: Percentage deviation from expected.
        description:       Human-readable summary.
        detected_at:       When the anomaly was flagged.
        resolved:          Whether it has been acknowledged/resolved.
    """

    __tablename__ = "anomaly_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    ward = Column(String(100), nullable=False)
    department = Column(String(255), nullable=True)
    anomaly_type = Column(String(50), nullable=False, default="spike")
    severity = Column(
        Enum(AnomalySeverity, name="anomaly_severity_enum", native_enum=False),
        nullable=False,
        default=AnomalySeverity.WARNING,
    )
    expected_value = Column(Float, nullable=False, default=0.0)
    actual_value = Column(Float, nullable=False, default=0.0)
    deviation_percent = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=True)
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved = Column(Integer, nullable=False, default=0)  # 0=unresolved, 1=resolved

    __table_args__ = (
        Index("ix_anomaly_logs_ward", "ward"),
        Index("ix_anomaly_logs_severity", "severity"),
        Index("ix_anomaly_logs_detected_at", "detected_at"),
        Index("ix_anomaly_logs_resolved", "resolved"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnomalyLog(ward={self.ward}, type={self.anomaly_type}, "
            f"severity={self.severity}, detected_at={self.detected_at})>"
        )
