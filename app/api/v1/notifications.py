"""
NAYAM (नयम्) — Notifications API Route.

Single lightweight endpoint that aggregates events for the bell icon.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationsResponse
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=NotificationsResponse,
    summary="Get aggregated notifications",
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationsResponse:
    """
    Returns recent high-signal events for the notification bell:
    - Pending AI action approvals
    - High / Critical open issues
    - Recently uploaded documents
    """
    service = NotificationService(db)
    return service.get_notifications()
