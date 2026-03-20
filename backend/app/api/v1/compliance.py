"""
NAYAM (नयम्) — Compliance API Routes (Phase 4).

Endpoints for compliance export lifecycle: request, track, list.
"""

import io
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.compliance.models import ExportStatus
from app.compliance.audit_trail_pdf import generate_audit_trail_pdf
from app.models.user import User, UserRole
from app.models.action_request import ActionRequest
from app.schemas.compliance import (
    ComplianceExportRequest,
    ComplianceExportResponse,
    ComplianceExportListResponse,
)
from app.compliance.service import ComplianceService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/exports",
    response_model=ComplianceExportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a compliance export",
)
def request_export(
    payload: ComplianceExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.ANALYST])),
) -> ComplianceExportResponse:
    """Create a new compliance export request."""
    svc = ComplianceService(db)
    export = svc.request_export(
        user_id=current_user.id,
        report_type=payload.report_type,
        export_format=payload.export_format,
        parameters=payload.parameters,
    )
    return ComplianceExportResponse.model_validate(export)


@router.get(
    "/exports",
    response_model=ComplianceExportListResponse,
    summary="List compliance exports",
)
def list_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[ExportStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComplianceExportListResponse:
    """List compliance exports with optional status filter."""
    svc = ComplianceService(db)
    items, total = svc.list_all(skip=skip, limit=limit, status_filter=status_filter)
    return ComplianceExportListResponse(
        total=total,
        exports=[ComplianceExportResponse.model_validate(e) for e in items],
    )


@router.get(
    "/exports/mine",
    response_model=ComplianceExportListResponse,
    summary="My compliance exports",
)
def my_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComplianceExportListResponse:
    """List exports requested by the current user."""
    svc = ComplianceService(db)
    items, total = svc.list_by_user(current_user.id, skip=skip, limit=limit)
    return ComplianceExportListResponse(
        total=total,
        exports=[ComplianceExportResponse.model_validate(e) for e in items],
    )


@router.get(
    "/exports/{export_id}",
    response_model=ComplianceExportResponse,
    summary="Get export details",
)
def get_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComplianceExportResponse:
    """Retrieve a single compliance export by ID."""
    svc = ComplianceService(db)
    return ComplianceExportResponse.model_validate(svc.get_export(export_id))


@router.get(
    "/audit-trail/pdf",
    summary="Export audit trail as PDF",
)
def export_audit_trail_pdf(
    include_hindi: bool = Query(True, description="Include Hindi translations in PDF"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.LEADER, UserRole.ANALYST])),
) -> StreamingResponse:
    """
    Generate and download a PDF report of the last 50 audit trail entries.
    
    Query Parameters:
        include_hindi: Include Hindi translations (default: true)
    
    The PDF includes:
    - NAYAM header with branding
    - Generation timestamp and user info
    - Table of audit entries with: timestamp, actor, action, type (AI/Human), status
    - Page numbers and pagination
    - Optional Hindi subtitle (नयम् - शासन प्रबंधन प्रणाली)
    """
    # Fetch last 50 action requests, ordered by creation date (newest first)
    audit_entries = (
        db.query(ActionRequest)
        .options(joinedload(ActionRequest.requester))
        .order_by(desc(ActionRequest.created_at))
        .limit(50)
        .all()
    )

    # Generate PDF with optional hindi support
    pdf_bytes = generate_audit_trail_pdf(
        audit_entries=audit_entries,
        user=current_user,
        generated_at=datetime.now(timezone.utc),
        include_hindi=include_hindi,
    )

    # Return as downloadable file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"NAYAM_AuditTrail_{timestamp}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
