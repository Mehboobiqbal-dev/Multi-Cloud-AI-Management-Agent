#!/bin/bash

# Set memory optimization environment variables
export ENABLE_LOCAL_EMBEDDINGS=false
export ENABLE_MEMORY_OPTIMIZATIONS=true
export LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2

# Set PyTorch memory optimization flags
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:32
export PYTORCH_NO_CUDA_MEMORY_CACHING=1

# Set Python memory optimization flags
export PYTHONMALLOC=malloc
export PYTHONUNBUFFERED=1

# Initialize database
python -c "from core.db import init_db; init_db()" || true

# Start the application with memory-optimized settings
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 300 \
  --keep-alive 5 \
  --max-requests 100 \
  --preload \
  --log-level info \
  --access-logfile - \
  --error-logfile -