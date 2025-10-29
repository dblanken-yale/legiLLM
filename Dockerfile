# LegiScan Bill Analysis Pipeline - Docker Image
# Multi-stage build for optimized production image

FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - minimal runtime image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY prompts/ ./prompts/
COPY config.json .

# Create directories for data (will be mounted or use storage provider)
RUN mkdir -p data/raw data/filtered data/analyzed data/cache/legiscan_cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default storage backend (can be overridden)
ENV STORAGE_BACKEND=local

# Health check (optional - checks if Python and dependencies are available)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from src.storage_provider import StorageProviderFactory; sys.exit(0)"

# Default command - can be overridden at runtime
# Examples:
#   docker run image python scripts/fetch_legiscan_bills.py
#   docker run image python scripts/run_filter_pass.py ct_bills_2025
#   docker run image python scripts/run_analysis_pass.py
CMD ["python", "--version"]

# Labels for metadata
LABEL maintainer="LegiScan Analysis Team"
LABEL description="LegiScan Bill Analysis Pipeline with Azure deployment support"
LABEL version="1.0"
