# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy only requirements for dependency install
COPY requirements-render.txt requirements.txt

# Install dependencies with memory optimizations
RUN pip install --no-cache-dir --no-deps -r requirements.txt \
    && pip cache purge

# Copy only necessary source code (exclude tests, docs, venv, .git, etc.)
COPY . .
RUN rm -rf tests docs venv .git

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages and app from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /app /app

# Make scripts executable
RUN chmod +x start-render-optimized.sh

# Set memory optimization environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    PYTHONHASHSEED=0 \
    MALLOC_TRIM_THRESHOLD_=50000 \
    MALLOC_MMAP_THRESHOLD_=65536 \
    ENABLE_MEMORY_OPTIMIZATIONS=true \
    HIGH_MEMORY_MODE=false \
    ENABLE_LOCAL_EMBEDDINGS=false \
    NO_MEMORY=true

# Expose port
EXPOSE 8000

# Health check with memory consideration
HEALTHCHECK --interval=60s --timeout=15s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Use optimized start script for 512MB memory limit
CMD ["./start-render-optimized.sh"]
