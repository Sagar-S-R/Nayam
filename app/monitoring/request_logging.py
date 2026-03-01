"""
NAYAM (नयम्) — Request Logging Middleware (Phase 4).

Injects a unique ``X-Request-ID`` header into every request/response
and logs request/response details via structlog for observability.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, bind_request_context, clear_request_context

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that:

    1. Generates (or reads) a unique ``X-Request-ID`` for every request.
    2. Binds the request ID to the structlog context for correlation.
    3. Logs the request path, method, status code, and latency.
    4. Echoes the request ID back in the response headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use an incoming header if present, otherwise generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind to structlog context
        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request.unhandled_error")
            raise
        finally:
            latency_ms = round((time.monotonic() - start) * 1000, 2)
            logger.info(
                "request.completed",
                status_code=getattr(response, "status_code", 500) if "response" in dir() else 500,
                latency_ms=latency_ms,
            )
            clear_request_context()

        response.headers["X-Request-ID"] = request_id
        return response
