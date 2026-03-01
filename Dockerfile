# NAYAM (नयम्) — Production Dockerfile
# Multi-stage build for minimal image size and security.
# =====================================================================

# ── Stage 1: Build dependencies ──────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Install system dependencies for psycopg2 and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

LABEL maintainer="NAYAM Team"
LABEL version="4.0"
LABEL description="NAYAM — Secure AI Co-Pilot for Public Leaders & Administrators"

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r nayam && useradd -r -g nayam -m nayam

WORKDIR /app

# Copy application code
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY app/ ./app/

# Create writable directories
RUN mkdir -p uploads exports && chown -R nayam:nayam /app

USER nayam

# Environment defaults (overridden by docker-compose / k8s)
ENV APP_ENV=production \
    APP_NAME=NAYAM \
    APP_VERSION=4.0.0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Health check — uses the lightweight /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn — production settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--access-log"]
