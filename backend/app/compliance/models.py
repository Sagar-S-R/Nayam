"""
NAYAM (नयम्) — ComplianceExport ORM Model (Phase 4).

Tracks compliance report generation requests and their artefacts.
Supports FR4-004: exportable compliance reports with immutable records.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Index, Integer, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base


class ExportFormat(str, enum.Enum):
    """Supported compliance export formats."""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


class ExportStatus(str, enum.Enum):
    """Lifecycle state of an export job."""
    REQUESTED = "requested"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ComplianceExport(Base):
    """
    Compliance report export record.

    Attributes:
        id:              UUID primary key.
        requested_by:    UUID of the requesting user.
        report_type:     Category (e.g. "audit_summary", "access_log", "full_dump").
        export_format:   Output format.
        status:          Job lifecycle state.
        parameters:      JSON filter parameters (date range, ward, etc.).
        record_count:    Number of records included in the export.
        file_path:       Path to the generated artefact (if completed).
        file_size_bytes: Size of the generated file.
        error_message:   Failure reason (if any).
        requested_at:    When the export was requested.
        completed_at:    When the export finished.
    """

    __tablename__ = "compliance_exports"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    requested_by = Column(Uuid, nullable=False)
    report_type = Column(String(100), nullable=False)
    export_format = Column(
        Enum(ExportFormat, name="export_format_enum", native_enum=False),
        nullable=False,
        default=ExportFormat.JSON,
    )
    status = Column(
        Enum(ExportStatus, name="export_status_enum", native_enum=False),
        nullable=False,
        default=ExportStatus.REQUESTED,
    )
    parameters = Column(JSON, nullable=True)
    record_count = Column(Integer, nullable=True, default=0)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True, default=0)
    error_message = Column(Text, nullable=True)
    requested_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_compliance_exports_requested_by", "requested_by"),
        Index("ix_compliance_exports_report_type", "report_type"),
        Index("ix_compliance_exports_status", "status"),
        Index("ix_compliance_exports_requested_at", "requested_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceExport(type={self.report_type}, format={self.export_format}, "
            f"status={self.status}, requested_at={self.requested_at})>"
        )
