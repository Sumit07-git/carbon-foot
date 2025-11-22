# ============================================================================
# DOCKERFILE - CARBON FOOTPRINT MONITOR
# ============================================================================
# Build: docker build -t carbon-monitor .
# Run: docker run -p 5000:5000 carbon-monitor
# ============================================================================

# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set metadata
LABEL maintainer="Carbon Monitor Team"
LABEL description="Carbon Footprint Monitor - Flask Application with ML"
LABEL version="1.0.0"

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ============================================================================
# INSTALL SYSTEM DEPENDENCIES
# ============================================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    wget \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# COPY PROJECT FILES
# ============================================================================

# Copy requirements first for better caching
COPY requirements.txt .

# ============================================================================
# INSTALL PYTHON DEPENDENCIES
# ============================================================================

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# ============================================================================
# COPY APPLICATION FILES
# ============================================================================

# Copy all application files
COPY app.py .
COPY ml_model.py .
COPY database.py .
COPY config.py .

# Copy templates
COPY templates/ /app/templates/

# Copy static files
COPY static/ /app/static/

# ============================================================================
# CREATE NECESSARY DIRECTORIES
# ============================================================================

RUN mkdir -p \
    data \
    models \
    logs \
    backups \
    exports

# ============================================================================
# CREATE NON-ROOT USER FOR SECURITY
# ============================================================================

# Create appuser for running the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# ============================================================================
# EXPOSE PORT
# ============================================================================

EXPOSE 5000

# ============================================================================
# HEALTH CHECK
# ============================================================================

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# ============================================================================
# RUN APPLICATION
# ============================================================================

# Use Gunicorn as production server
# 4 worker processes, bind to 0.0.0.0:5000
CMD ["gunicorn", \
     "-w", "4", \
     "-b", "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "app:app"]

# ============================================================================
# BUILD INSTRUCTIONS
# ============================================================================
#
# Build the Docker image:
#   docker build -t carbon-monitor .
#   docker build -t carbon-monitor:latest .
#   docker build -t carbon-monitor:1.0 .
#
# Run the container:
#   docker run -p 5000:5000 carbon-monitor
#   docker run -d -p 5000:5000 --name carbon-app carbon-monitor
#   docker run -d -p 5000:5000 -v $(pwd)/data:/app/data carbon-monitor
#
# Run with environment file:
#   docker run -p 5000:5000 --env-file .env carbon-monitor
#
# Access the application:
#   http://localhost:5000
#
# View logs:
#   docker logs carbon-app
#   docker logs -f carbon-app
#
# Stop container:
#   docker stop carbon-app
#
# Remove container:
#   docker rm carbon-app
#
# ============================================================================