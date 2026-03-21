###############################################################################
# Bruce AI Backend - Production Dockerfile
# Multi-stage build for Python 3.12 FastAPI application
###############################################################################

# ── Stage 1: Builder ─────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r bruce && useradd -r -g bruce -d /app -s /sbin/nologin bruce

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY main.py .
COPY config/ ./config/
COPY auth.py ./
COPY app/ ./app/
COPY ai/ ./ai/
COPY ai_core/ ./ai_core/
COPY modules/ ./modules/
COPY data/ ./data/

# Copy top-level Python modules
COPY bruce_agent.py ./
COPY orchestrator.py ./

# Create directories for runtime data
RUN mkdir -p /app/data /app/logs /app/uploads /app/models /app/vector_db \
    && chown -R bruce:bruce /app

# Switch to non-root user
USER bruce

# Expose API port
EXPOSE 8000

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Run uvicorn with production settings
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
