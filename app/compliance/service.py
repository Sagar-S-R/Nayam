"""
NAYAM (नयम्) — Compliance Service (Phase 4).

Business logic for compliance report export lifecycle.
Supports FR4-004: exportable compliance reports with immutable records.
"""

import logging
import os
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.compliance.models import ComplianceExport, ExportFormat, ExportStatus
from app.compliance.repository import ComplianceExportRepository

logger = logging.getLogger(__name__)


class ComplianceService:
    """Orchestrates compliance export creation and retrieval."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ComplianceExportRepository(db)
        self.settings = get_settings()

    # ── Export Lifecycle ──────────────────────────────────────────

    def request_export(
        self,
        user_id: UUID,
        report_type: str,
        export_format: ExportFormat = ExportFormat.JSON,
        parameters: Optional[dict] = None,
    ) -> ComplianceExport:
        """Create a new export request."""
        export = ComplianceExport(
            requested_by=user_id,
            report_type=report_type,
            export_format=export_format,
            parameters=parameters,
        )
        return self.repo.create(export)

    def get_export(self, export_id: UUID) -> ComplianceExport:
        export = self.repo.get_by_id(export_id)
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compliance export {export_id} not found",
            )
        return export

    def begin_processing(self, export_id: UUID) -> ComplianceExport:
        export = self.get_export(export_id)
        if export.status != ExportStatus.REQUESTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Export is {export.status.value}, expected REQUESTED",
            )
        return self.repo.mark_processing(export)

    def complete_export(
        self,
        export_id: UUID,
        file_path: str,
        file_size_bytes: int,
        record_count: int,
    ) -> ComplianceExport:
        export = self.get_export(export_id)
        if export.status != ExportStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Export is {export.status.value}, expected PROCESSING",
            )
        return self.repo.mark_completed(export, file_path, file_size_bytes, record_count)

    def fail_export(self, export_id: UUID, error: str) -> ComplianceExport:
        export = self.get_export(export_id)
        return self.repo.mark_failed(export, error)

    # ── Queries ──────────────────────────────────────────────────

    def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[ComplianceExport], int]:
        return self.repo.get_by_user(user_id, skip=skip, limit=limit)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[ExportStatus] = None,
    ) -> Tuple[List[ComplianceExport], int]:
        return self.repo.get_all(skip=skip, limit=limit, status_filter=status_filter)

    def get_export_dir(self) -> str:
        """Return (and ensure existence of) the compliance export directory."""
        export_dir = self.settings.COMPLIANCE_EXPORT_DIR
        os.makedirs(export_dir, exist_ok=True)
        return export_dir
