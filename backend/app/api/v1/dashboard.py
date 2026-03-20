"""
NAYAM (नयम्) — Dashboard API Routes.

Aggregation endpoints for the admin dashboard.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=DashboardResponse,
    summary="Get dashboard aggregation",
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    Get aggregated dashboard data including issue stats and recent documents.

    Returns:
        Total issues, issues by department/status, and recent documents.

    Requires: Any authenticated user.
    """
    service = DashboardService(db)
    return service.get_dashboard()
