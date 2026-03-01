"""
NAYAM (नयम्) — AuditLog ORM Model (Phase 3).

Immutable append-only audit trail for all security-sensitive operations.
Satisfies FR3-003 (data access logging) and NFR (immutable audit logs).
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Index, String, Text, Uuid,
)
from sqlalchemy.dialects.postgresql import JSON

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Categories of auditable events."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    DECRYPT = "decrypt"
    EXPORT = "export"
    APPROVE = "approve"
    REJECT = "reject"


class AuditLog(Base):
    """
    Immutable audit log entry.

    Records are append-only; there is no UPDATE/DELETE API exposed.

    Attributes:
        id:             UUID primary key.
        user_id:        UUID of the acting user (nullable for system events).
        action:         Auditable action category.
        resource_type:  Entity type affected (e.g. "citizen", "issue").
        resource_id:    UUID of the affected record.
        description:    Human-readable summary.
        ip_address:     Client IP (if available).
        user_agent:     Client user-agent header.
        metadata:       Additional context as JSON.
        created_at:     Immutable timestamp.
    """

    __tablename__ = "audit_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(Uuid, nullable=True)
    action = Column(
        Enum(AuditAction, name="audit_action_enum", native_enum=False),
        nullable=False,
    )
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource_type", "resource_type"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(action={self.action}, resource={self.resource_type}, "
            f"user_id={self.user_id}, at={self.created_at})>"
        )
