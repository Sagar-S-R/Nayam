"""
NAYAM (नयम्) — Compliance Pydantic Schemas (Phase 4).

Request / response models for compliance export lifecycle.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.compliance.models import ExportFormat, ExportStatus


class ComplianceExportRequest(BaseModel):
    """Request body to create a compliance export."""
    report_type: str = Field(..., min_length=1, max_length=100)
    export_format: ExportFormat = ExportFormat.JSON
    parameters: Optional[Dict[str, Any]] = None


class ComplianceExportResponse(BaseModel):
    """Single compliance export in responses."""
    id: UUID
    requested_by: UUID
    report_type: str
    export_format: ExportFormat
    status: ExportStatus
    parameters: Optional[Dict[str, Any]]
    record_count: Optional[int]
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    error_message: Optional[str]
    requested_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ComplianceExportListResponse(BaseModel):
    """Paginated compliance export list."""
    total: int
    exports: List[ComplianceExportResponse]
