###############################################################################
# Bruce AI Backend - Production Dockerfile
###############################################################################

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY *.py ./
COPY app/ ./app/
COPY ai/ ./ai/
COPY ai_core/ ./ai_core/
COPY modules/ ./modules/
COPY plugins/ ./plugins/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Create directories for runtime data
RUN mkdir -p /app/logs /app/uploads /app/models

# Expose API port
EXPOSE 8000

# Use tini for proper signal handling
ENTRYPOINT ["tini", "--"]

# Run uvicorn
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
