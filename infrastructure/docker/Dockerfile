### Production-ready Dockerfile for AI Trading System ###

# Base image with Python 3.12 & necessary dependencies
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirement files & install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose API port
EXPOSE 8000

# Set environment variables (security best practices)
ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production

# Run the FastAPI app with Gunicorn for scalability
CMD ["gunicorn", "app.main:app", "--workers=4", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]

# 🔒 Seguridad, Logging y Producción
RUN pip install gunicorn uvicorn