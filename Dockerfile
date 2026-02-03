# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

# =============================================================================
# Stage 1: Build stage
# =============================================================================
FROM python:3.14-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libpango1.0-dev \
    libcairo2-dev \
    libgdk-pixbuf2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory for build
WORKDIR /build

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Runtime stage
# =============================================================================
FROM python:3.14-slim AS runtime

# Install only runtime dependencies required by weasyprint and other libraries
# Also install tini as a minimal init system for proper signal handling
# Install PostgreSQL and MySQL clients for database backups
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi8 \
    fonts-dejavu-core \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash coati

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=coati:coati . .

# Switch to non-root user
USER coati

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the application
CMD ["python", "app.py"]
