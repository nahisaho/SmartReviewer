# SmartReviewer Dockerfile
# Multi-stage build for MCP-based Document Review AI Agent

# ============================================
# Base Stage
# ============================================
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ============================================
# Development Stage
# ============================================
FROM base as development

# Install dev dependencies
RUN pip install --no-cache-dir ".[dev]"

# Copy source code (mounted as volume in development)
COPY src/ ./src/
COPY tests/ ./tests/

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "-m", "smartreviewer.servers.core"]

# ============================================
# Production Stage
# ============================================
FROM base as production

# Copy source code
COPY src/ ./src/

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT:-8000}/health || exit 1

# Default command
CMD ["python", "-m", "smartreviewer.servers.core"]
