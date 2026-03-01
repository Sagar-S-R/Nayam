"""
NAYAM (नयम्) — Structured Logging Configuration (Phase 4).

Provides a unified structlog setup with:
  • JSON output in production, pretty console output in development
  • Request-ID correlation via context variables
  • Timestamper, log-level canonicalisation, exception rendering
  • Drop-in replacement for stdlib logging when needed

Usage::

    from app.core.logging import get_logger, configure_logging

    configure_logging(json_output=True)  # call once at startup
    logger = get_logger(__name__)
    logger.info("event.happened", user_id="abc-123", latency_ms=42.5)
"""

import logging
import sys
from typing import Optional

import structlog


def configure_logging(
    json_output: bool = False,
    log_level: str = "INFO",
) -> None:
    """
    Configure structlog and stdlib logging for the entire application.

    Args:
        json_output: If True, emit JSON lines (production). Otherwise
                     use coloured console output (development).
        log_level:   Root log level string (DEBUG, INFO, WARNING, …).
    """
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Quiet noisy third-party loggers
    for name in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Return a structlog bound logger for the given module name.

    Args:
        name: Logger name, typically ``__name__``.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, **extra) -> None:
    """
    Bind request-scoped context variables that will appear in every
    subsequent log line within the same async / sync context.
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, **extra)


def clear_request_context() -> None:
    """Clear all request-scoped context variables."""
    structlog.contextvars.clear_contextvars()
