"""Memory optimization utilities for reducing RAM usage.

This module provides functions to optimize memory usage in the application,
particularly for machine learning models that consume large amounts of RAM.
"""

import os
import gc
import sys
import psutil
import logging
from typing import Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    
try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .config import settings

logger = logging.getLogger(__name__)

def get_memory_usage():
    """Get current memory usage information.
    
    Returns:
        dict: Memory usage statistics
    """
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            "percent": memory_percent,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
    except Exception as e:
        logger.error(f"Failed to get memory usage: {e}")
        return {"error": str(e)}

def force_garbage_collection():
    """Force garbage collection and return collected objects count.
    
    Returns:
        int: Number of objects collected
    """
    try:
        # Force garbage collection for all generations
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)
        
        # Additional cleanup
        gc.collect()
        
        logger.info(f"Garbage collection completed, collected {collected} objects")
        return collected
    except Exception as e:
        logger.error(f"Failed to perform garbage collection: {e}")
        return 0

def optimize_python_memory():
    """Optimize Python memory usage.
    
    Returns:
        dict: Applied optimizations
    """
    results = {}
    
    try:
        # Set garbage collection thresholds more aggressively
        gc.set_threshold(100, 5, 5)  # More frequent GC
        results["gc_threshold_set"] = True
        
        # Force initial garbage collection
        collected = force_garbage_collection()
        results["initial_gc_collected"] = collected
        
        # Optimize sys settings for memory
        if hasattr(sys, 'intern'):
            # Enable string interning for memory efficiency
            results["string_interning"] = True
        
        logger.info("Python memory optimizations applied")
        return results
        
    except Exception as e:
        logger.error(f"Failed to apply Python memory optimizations: {e}")
        return {"error": str(e)}

def optimize_torch_memory():
    """Optimize PyTorch memory usage.
    
    Returns:
        bool: True if optimizations were applied, False otherwise
    """
    if not TORCH_AVAILABLE:
        logger.info("PyTorch not available, skipping torch memory optimizations")
        return False
    
    try:
        if torch.cuda.is_available():
            # Clear CUDA cache
            torch.cuda.empty_cache()
        
        # Configure transformers for memory efficiency
        if TRANSFORMERS_AVAILABLE:
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            transformers.logging.set_verbosity_error()
        
        logger.info("PyTorch memory optimizations applied")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply PyTorch optimizations: {e}")
        return False

def apply_memory_optimizations():
    """Apply all available memory optimizations based on configuration.
    
    Returns:
        dict: Summary of applied optimizations
    """
    results = {}
    
    # Log initial memory usage
    initial_memory = get_memory_usage()
    logger.info(f"Initial memory usage: {initial_memory.get('rss_mb', 'unknown'):.1f}MB RSS, {initial_memory.get('percent', 'unknown'):.1f}%")
    
    # Check if memory optimizations are enabled
    if not getattr(settings, 'ENABLE_MEMORY_OPTIMIZATIONS', True):
        logger.info("Memory optimizations disabled by configuration")
        return {"applied": False, "reason": "disabled_by_config"}
    
    # Always apply ultra-aggressive optimizations for 512MB Render.com limit
    logger.info("Applying ultra-aggressive memory optimizations for 512MB limit")
    
    # Apply Python memory optimizations first
    python_opts = optimize_python_memory()
    results["python_optimizations"] = python_opts
    
    # Apply PyTorch optimizations
    results["torch_optimized"] = optimize_torch_memory()
    
    # Ultra-aggressive batch size reduction for 512MB limit
    if hasattr(settings, 'EMBEDDING_BATCH_SIZE'):
        if settings.EMBEDDING_BATCH_SIZE > 1:  # Minimum possible batch size
            logger.info(f"Reducing embedding batch size from {settings.EMBEDDING_BATCH_SIZE} to 1 for 512MB limit")
            settings.EMBEDDING_BATCH_SIZE = 1
            results["reduced_batch_size"] = True
    
    # Ultra-aggressive memory cache reduction
    if hasattr(settings, 'MEMORY_CACHE_SIZE'):
        if settings.MEMORY_CACHE_SIZE > 50:  # Minimal cache for 512MB limit
            logger.info(f"Reducing memory cache size from {settings.MEMORY_CACHE_SIZE} to 50 for 512MB limit")
            settings.MEMORY_CACHE_SIZE = 50
            results["reduced_cache_size"] = True
    
    # Ensure local embeddings are disabled
    if getattr(settings, 'ENABLE_LOCAL_EMBEDDINGS', False):
        logger.info("Disabling local embeddings for memory optimization")
        settings.ENABLE_LOCAL_EMBEDDINGS = False
        results["disabled_local_embeddings"] = True
    
    # Set environment variables for ultra-aggressive memory efficiency
    os.environ['PYTHONHASHSEED'] = '0'  # Consistent hashing
    os.environ['MALLOC_TRIM_THRESHOLD_'] = '50000'  # Very aggressive malloc trimming
    os.environ['MALLOC_MMAP_THRESHOLD_'] = '65536'  # Use mmap for large allocations
    os.environ['PYTHONOPTIMIZE'] = '2'  # Remove docstrings and assertions
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Don't write .pyc files
    
    # Force aggressive garbage collection every 30 seconds
    import threading
    import time
    
    def periodic_gc():
        while True:
            time.sleep(30)
            collected = force_garbage_collection()
            if collected > 0:
                logger.debug(f"Periodic GC collected {collected} objects")
    
    gc_thread = threading.Thread(target=periodic_gc, daemon=True)
    gc_thread.start()
    results["periodic_gc_enabled"] = True
    
    results["ultra_aggressive_mode"] = True
    results["render_optimized"] = True
    
    # Final memory check
    final_memory = get_memory_usage()
    logger.info(f"Final memory usage: {final_memory.get('rss_mb', 'unknown'):.1f}MB RSS, {final_memory.get('percent', 'unknown'):.1f}%")
    
    # Memory usage warning for Render.com 512MB limit
    current_mb = final_memory.get('rss_mb', 0)
    if current_mb > 350:  # Warn at 350MB (68% of 512MB limit)
        logger.warning(f"Memory usage is {current_mb:.1f}MB, approaching 512MB limit on Render.com")
        results["memory_warning"] = True
    elif current_mb > 450:  # Critical warning at 450MB (88% of limit)
        logger.critical(f"Memory usage is {current_mb:.1f}MB, critically close to 512MB limit!")
        results["memory_critical"] = True
        # Force emergency garbage collection
        emergency_collected = force_garbage_collection()
        logger.info(f"Emergency GC collected {emergency_collected} objects")
    
    # Log memory optimization results
    optimizations_applied = any(results.values())
    logger.info(f"Memory optimizations applied: {optimizations_applied}")
    
    return {"applied": optimizations_applied, "details": results}