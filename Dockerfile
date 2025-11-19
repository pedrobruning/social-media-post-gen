# =============================================================================
# Multi-stage Dockerfile for Social Media Post Generation Agent
# =============================================================================
# This Dockerfile uses a multi-stage build to keep the final image size small
# while still leveraging UV for fast, reproducible dependency management.

# =============================================================================
# Stage 1: Builder - Install dependencies using UV
# =============================================================================
FROM python:3.12-slim AS builder

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to a virtual environment
# UV will create a .venv directory with all dependencies
RUN uv sync --frozen --no-dev

# =============================================================================
# Stage 2: Runtime - Create the final image
# =============================================================================
FROM python:3.12-slim

# Install system dependencies
# - libpq5: PostgreSQL client library for psycopg2
# - curl: For health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY main.py /app/main.py

# Create storage directory for images
RUN mkdir -p /app/storage/images && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Run the FastAPI application with uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
