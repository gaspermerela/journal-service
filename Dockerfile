# Multi-stage Dockerfile for AI Journal Backend Service
# Optimized for ARM64 architecture

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
# g++ needed for editdistpy (symspellpy dependency)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Dictionary Generator (Slovenian spell-check)
FROM python:3.11-slim AS dict-builder

WORKDIR /build

# Install datasets library for downloading Sloleks from HuggingFace
# Pin to 2.18.0 - newer versions removed support for custom dataset loading scripts (which Sloleks uses)
RUN pip install --no-cache-dir datasets==2.18.0

# Copy and run word list generation script
COPY scripts/generate_slovenian_wordlist.py .
RUN python generate_slovenian_wordlist.py --output /build/sl-words.txt

# Stage 3: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH

# Install runtime dependencies (FFmpeg for Whisper audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data/audio && \
    mkdir -p /app/data/dictionaries && \
    mkdir -p /app/data/cache && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy Slovenian word list from dict-builder
COPY --from=dict-builder --chown=appuser:appuser /build/sl-words.txt /app/data/dictionaries/sl-words.txt

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# No CMD or HEALTHCHECK - defined in docker-compose files for flexibility
