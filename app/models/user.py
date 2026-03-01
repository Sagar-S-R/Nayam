"""
NAYAM (नयम्) — User ORM Model.

Defines the User table with UUID primary key, role-based access,
and bcrypt password hash storage.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Enum, DateTime, Index, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Enumeration of user roles for RBAC."""
    LEADER = "Leader"
    STAFF = "Staff"
    ANALYST = "Analyst"


class User(Base):
    """
    User ORM model.

    Attributes:
        id: UUID primary key.
        name: Full name of the user.
        email: Unique email address.
        password_hash: Bcrypt-hashed password.
        role: Role enum (Leader, Staff, Analyst).
        created_at: Timestamp of account creation.
    """

    __tablename__ = "users"

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    role = Column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        nullable=False,
        default=UserRole.STAFF,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    documents = relationship(
        "Document",
        back_populates="uploader",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
