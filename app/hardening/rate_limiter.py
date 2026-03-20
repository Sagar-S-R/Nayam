"""
NAYAM (नयम्) — Rate Limiter Middleware (Phase 4).

Implements per-IP / per-endpoint API throttling and records
rate-limit events to the database for auditing.

Design references: FR4-003 (rate limiting and API throttling).
"""

import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.hardening.models import RateLimitRecord

logger = logging.getLogger(__name__)

# ── In-memory sliding window (lightweight, no Redis dependency) ──

_request_store: dict = {}  # key: ip -> list of timestamps


def _is_rate_limited(client_ip: str, max_requests: int, window_seconds: int) -> bool:
    """Check if *client_ip* exceeds *max_requests* within *window_seconds*."""
    now = time.time()
    cutoff = now - window_seconds

    timestamps = _request_store.get(client_ip, [])
    # Prune expired entries
    timestamps = [t for t in timestamps if t > cutoff]
    timestamps.append(now)
    _request_store[client_ip] = timestamps

    return len(timestamps) > max_requests


def reset_rate_limiter() -> None:
    """Clear the in-memory request store.  Useful for testing."""
    _request_store.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that enforces per-IP rate limits.

    * Reads thresholds from Settings (RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS).
    * On breach, returns **429 Too Many Requests** and optionally records the
      event to the ``rate_limit_records`` table when a DB session factory is
      provided.
    """

    def __init__(
        self,
        app,
        db_session_factory: Optional[Callable] = None,
    ) -> None:
        super().__init__(app)
        self.db_session_factory = db_session_factory

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()

        if settings.RATE_LIMIT_REQUESTS <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"        
        endpoint = request.url.path

        # Determine limits based on endpoint
        if endpoint.startswith("/api/v1/agent"):
            max_requests = 10  # Stricter for Agent
            window = 60
            
            # Try to get user_id from token
            user_id = client_ip
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    import jwt
                    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                    user_id = payload.get("sub", client_ip)
                except:
                    pass
            rate_key = f"agent:{user_id}"
        else:
            max_requests = settings.RATE_LIMIT_REQUESTS
            window = settings.RATE_LIMIT_WINDOW_SECONDS
            rate_key = client_ip

        if _is_rate_limited(rate_key, max_requests, window):
            logger.warning(
                "Rate limit exceeded: key=%s endpoint=%s", rate_key, endpoint,  
            )
            self._record_event(client_ip, endpoint, window, blocked=True)       
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},    
            )

        response = await call_next(request)
        return response

    # ── Persistence (fire-and-forget) ────────────────────────────

    def _record_event(
        self,
        client_ip: str,
        endpoint: str,
        window: int,
        blocked: bool,
    ) -> None:
        """Persist a rate-limit event if a DB factory is available."""
        if not self.db_session_factory:
            return
        try:
            db = self.db_session_factory()
            record = RateLimitRecord(
                client_ip=client_ip,
                endpoint=endpoint,
                window_seconds=window,
                blocked=1 if blocked else 0,
            )
            db.add(record)
            db.commit()
            db.close()
        except Exception as exc:
            logger.error("Failed to record rate-limit event: %s", exc)
