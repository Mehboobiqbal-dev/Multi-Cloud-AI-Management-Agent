# Memory Optimization Configuration

This document explains how to configure memory optimization settings for the Multi-Cloud AI Management Agent.

## HIGH_MEMORY_MODE Configuration

The `HIGH_MEMORY_MODE` setting in your `.env` file controls the level of memory optimization applied by the application.

### Configuration Options

#### HIGH_MEMORY_MODE=false (Recommended for low-memory systems)

When set to `false`, the application applies aggressive memory optimizations:

- **Embedding Batch Size**: Reduced to 4 (from default 10)
- **Memory Cache Size**: Reduced to 500 (from default 1000)
- **Local Embeddings**: Automatically disabled
- **PyTorch Memory**: Optimized with float16 tensors
- **Transformers**: Configured for memory efficiency

```env
HIGH_MEMORY_MODE=false
```

#### HIGH_MEMORY_MODE=true (Standard mode)

When set to `true`, the application applies standard memory optimizations:

- **Embedding Batch Size**: Reduced to 8 (if originally > 8)
- **Memory Cache Size**: Uses default settings
- **Local Embeddings**: Warning issued if enabled
- **PyTorch Memory**: Optimized with float16 tensors
- **Transformers**: Configured for memory efficiency

```env
HIGH_MEMORY_MODE=true
```

### Related Settings

These settings work in conjunction with `HIGH_MEMORY_MODE`:

```env
# Memory optimization control
ENABLE_MEMORY_OPTIMIZATIONS=true

# Embedding settings (automatically adjusted based on HIGH_MEMORY_MODE)
EMBEDDING_BATCH_SIZE=10
MEMORY_CACHE_SIZE=1000

# Local embeddings (disabled when HIGH_MEMORY_MODE=false)
ENABLE_LOCAL_EMBEDDINGS=false
LOCAL_EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2
```

### When to Use Each Mode

#### Use HIGH_MEMORY_MODE=false when:
- Running on systems with limited RAM (< 8GB)
- Experiencing out-of-memory errors
- Running multiple applications simultaneously
- Using cloud instances with memory constraints
- Performance is less critical than stability

#### Use HIGH_MEMORY_MODE=true when:
- Running on systems with ample RAM (>= 16GB)
- Performance is critical
- Memory usage is not a concern
- Running dedicated AI workloads

### Monitoring Memory Usage

The application logs memory optimization decisions during startup:

```
[INFO] HIGH_MEMORY_MODE is false - applying aggressive memory optimizations
[INFO] Reducing embedding batch size from 10 to 4
[INFO] Reducing memory cache size from 1000 to 500
[INFO] Disabling local embeddings for memory optimization
[INFO] Memory optimizations applied: True
```

### Troubleshooting

If you're still experiencing memory issues with `HIGH_MEMORY_MODE=false`:

1. Ensure `ENABLE_LOCAL_EMBEDDINGS=false`
2. Consider reducing `EMBEDDING_BATCH_SIZE` further (minimum: 1)
3. Reduce `MEMORY_CACHE_SIZE` further (minimum: 100)
4. Monitor system memory usage during operation
5. Consider upgrading system RAM if possible

### Performance Impact

Setting `HIGH_MEMORY_MODE=false` may result in:
- Slightly slower embedding processing (smaller batches)
- More frequent cache misses (smaller cache)
- Reduced memory footprint
- Improved system stability on low-memory systems

The performance impact is typically minimal compared to the stability benefits on memory-constrained systems.


### Render.com Specific Optimizations

For Render.com deployments, especially on free tier with 512MB RAM limit:

- Set `HIGH_MEMORY_MODE=false` in your service environment variables
- Ensure `ENABLE_LOCAL_EMBEDDINGS=false` to avoid loading heavy models
- Use the optimized start command: `./start-render-optimized.sh`
- Monitor build and deploy times; if timeouts occur, optimize dependencies in `requirements-render.txt`
- Add resource limits in `render.yaml`:
  plan: free
  numInstances: 1
- If deployment times out, check startup logs for memory issues and reduce initial load operations

For troubleshooting timeouts, refer to Render's documentation.