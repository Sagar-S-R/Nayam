"""
NAYAM (नयम्) — Audit Trail Write Helper.

Provides a single write_audit() function that inserts a row into the
existing audit_logs table (app.observability.models.AuditLog) so every
state-changing operation is traceable.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.observability.models import AuditLog, AuditAction

logger = logging.getLogger(__name__)


def write_audit(
    db: Session,
    *,
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    user_id: Optional[UUID] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Append a single immutable audit log entry.

    Silently swallows exceptions so a logging failure never breaks the
    primary operation.

    Args:
        db:            SQLAlchemy session (must already be within a transaction).
        action:        AuditAction enum value.
        resource_type: e.g. "issue", "citizen", "document", "draft", "action_request".
        resource_id:   String UUID of the affected record.
        description:   Human-readable detail shown on the Compliance page.
        user_id:       UUID of the acting user; None for system / AI events.
        metadata:      Optional extra JSON context.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            description=description,
            metadata_json=metadata or {},
        )
        db.add(entry)
        db.commit()  # Ensure persistence even if repository committed before us
    except Exception as exc:
        db.rollback()
        logger.warning("write_audit failed: %s", exc)
