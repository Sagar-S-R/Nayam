"""
NAYAM (नयम्) — ComplianceExport Repository (Phase 4).

Database operations for compliance report export lifecycle.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.compliance.models import ComplianceExport, ExportStatus

logger = logging.getLogger(__name__)


class ComplianceExportRepository:
    """Repository for ComplianceExport CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, export_id: UUID) -> Optional[ComplianceExport]:
        return self.db.query(ComplianceExport).filter(ComplianceExport.id == export_id).first()

    def create(self, export: ComplianceExport) -> ComplianceExport:
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        logger.info("Compliance export requested: id=%s type=%s", export.id, export.report_type)
        return export

    def mark_processing(self, export: ComplianceExport) -> ComplianceExport:
        export.status = ExportStatus.PROCESSING
        self.db.commit()
        self.db.refresh(export)
        return export

    def mark_completed(
        self,
        export: ComplianceExport,
        file_path: str,
        file_size_bytes: int,
        record_count: int,
    ) -> ComplianceExport:
        export.status = ExportStatus.COMPLETED
        export.file_path = file_path
        export.file_size_bytes = file_size_bytes
        export.record_count = record_count
        export.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(export)
        logger.info("Compliance export %s completed: %d records", export.id, record_count)
        return export

    def mark_failed(self, export: ComplianceExport, error: str) -> ComplianceExport:
        export.status = ExportStatus.FAILED
        export.error_message = error
        export.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(export)
        logger.error("Compliance export %s failed: %s", export.id, error)
        return export

    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 20) -> Tuple[List[ComplianceExport], int]:
        query = self.db.query(ComplianceExport).filter(ComplianceExport.requested_by == user_id)
        total = query.count()
        items = query.order_by(ComplianceExport.requested_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[ExportStatus] = None,
    ) -> Tuple[List[ComplianceExport], int]:
        query = self.db.query(ComplianceExport)
        if status_filter:
            query = query.filter(ComplianceExport.status == status_filter)
        total = query.count()
        items = query.order_by(ComplianceExport.requested_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def delete(self, export: ComplianceExport) -> None:
        self.db.delete(export)
        self.db.commit()
