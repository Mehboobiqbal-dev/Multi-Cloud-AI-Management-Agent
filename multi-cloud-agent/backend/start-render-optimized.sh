#!/bin/bash

# Ultra-aggressive memory optimization for 512MB Render.com limit
export ENABLE_LOCAL_EMBEDDINGS=false
export ENABLE_MEMORY_OPTIMIZATIONS=true
export HIGH_MEMORY_MODE=false
export NO_MEMORY=true

# Python memory optimization flags
export PYTHONMALLOC=malloc
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONOPTIMIZE=2
export PYTHONHASHSEED=0

# System memory optimization
export MALLOC_TRIM_THRESHOLD_=50000
export MALLOC_MMAP_THRESHOLD_=65536

# PyTorch memory optimization (if loaded)
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:16
export PYTORCH_NO_CUDA_MEMORY_CACHING=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# Transformers optimization (if loaded)
export TOKENIZERS_PARALLELISM=false
export TRANSFORMERS_CACHE=/tmp/transformers_cache

# Initialize database with minimal memory
python -c "from core.db import init_db; init_db()" || true

# Start with ultra-conservative settings for 512MB limit
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 120 \
  --keep-alive 2 \
  --max-requests 50 \
  --max-requests-jitter 10 \
  --preload \
  --worker-tmp-dir /dev/shm \
  --log-level warning \
  --access-logfile - \
  --error-logfile - \
  --worker-class uvicorn.workers.UvicornWorker