"""
NAYAM (नयम्) — RateLimitRecord ORM Model (Phase 4).

Tracks API rate-limiting events for security hardening.
Supports FR4-003: rate limiting and API throttling.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Index, Integer, String, Uuid,
)

from app.core.database import Base


class RateLimitRecord(Base):
    """
    Rate-limit event log.

    Each record captures a throttling window for an IP / user / API key
    so that the rate-limiting middleware can enforce quotas and the
    security team can audit abuse patterns.

    Attributes:
        id:              UUID primary key.
        client_ip:       Requesting client's IP address.
        user_id:         Authenticated user UUID (nullable for anonymous).
        endpoint:        API path being rate-limited.
        request_count:   Number of requests in the current window.
        window_seconds:  Duration of the rate-limit window.
        blocked:         Whether this event was a block (1) or pass (0).
        created_at:      When this record was created.
    """

    __tablename__ = "rate_limit_records"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, nullable=False)
    client_ip = Column(String(45), nullable=False)  # IPv4 or IPv6
    user_id = Column(Uuid, nullable=True)
    endpoint = Column(String(500), nullable=False)
    request_count = Column(Integer, nullable=False, default=1)
    window_seconds = Column(Integer, nullable=False, default=60)
    blocked = Column(Integer, nullable=False, default=0)  # 0=pass, 1=blocked
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_rate_limit_client_ip", "client_ip"),
        Index("ix_rate_limit_user_id", "user_id"),
        Index("ix_rate_limit_endpoint", "endpoint"),
        Index("ix_rate_limit_blocked", "blocked"),
        Index("ix_rate_limit_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<RateLimitRecord(ip={self.client_ip}, endpoint={self.endpoint}, "
            f"count={self.request_count}, blocked={bool(self.blocked)})>"
        )
