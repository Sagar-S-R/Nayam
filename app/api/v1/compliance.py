"""
NAYAM (नयम्) — Compliance API Routes (Phase 4).

Endpoints for compliance export lifecycle: request, track, list.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.compliance.models import ExportStatus
from app.models.user import User, UserRole
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
