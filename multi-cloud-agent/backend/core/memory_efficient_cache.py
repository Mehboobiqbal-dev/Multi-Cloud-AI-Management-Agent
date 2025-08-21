"""Memory-efficient caching and data structures for 512MB limit.

This module provides optimized caching strategies and data structures
that minimize memory usage while maintaining performance.
"""

import gc
import sys
import time
import weakref
import threading
from typing import Any, Dict, Optional, Union, List, Tuple
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Lightweight cache entry with minimal memory footprint."""
    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    
    def __post_init__(self):
        self.last_accessed = self.created_at
        # Estimate size (rough approximation)
        self.size_bytes = sys.getsizeof(self.value)

class MemoryEfficientLRUCache:
    """LRU Cache optimized for low memory usage."""
    
    def __init__(self, max_size: int = 100, max_memory_mb: int = 50, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._total_size_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with LRU update."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            current_time = time.time()
            
            # Check TTL
            if current_time - entry.created_at > self.ttl_seconds:
                self._remove_entry(key)
                self._misses += 1
                return None
            
            # Update access info
            entry.access_count += 1
            entry.last_accessed = current_time
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.value
    
    def put(self, key: str, value: Any) -> bool:
        """Put value in cache with memory management."""
        with self._lock:
            current_time = time.time()
            
            # Create new entry
            entry = CacheEntry(value=value, created_at=current_time)
            
            # Check if we need to evict existing entry
            if key in self._cache:
                old_entry = self._cache[key]
                self._total_size_bytes -= old_entry.size_bytes
            
            # Check memory limits before adding
            if (self._total_size_bytes + entry.size_bytes > self.max_memory_bytes or 
                len(self._cache) >= self.max_size):
                if not self._evict_entries(entry.size_bytes):
                    logger.warning(f"Cannot cache item of size {entry.size_bytes} bytes")
                    return False
            
            # Add to cache
            self._cache[key] = entry
            self._total_size_bytes += entry.size_bytes
            self._cache.move_to_end(key)
            
            return True
    
    def _remove_entry(self, key: str):
        """Remove entry and update size tracking."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._total_size_bytes -= entry.size_bytes
            self._evictions += 1
    
    def _evict_entries(self, needed_bytes: int) -> bool:
        """Evict entries to make space."""
        current_time = time.time()
        evicted_bytes = 0
        keys_to_remove = []
        
        # First, remove expired entries
        for key, entry in list(self._cache.items()):
            if current_time - entry.created_at > self.ttl_seconds:
                keys_to_remove.append(key)
                evicted_bytes += entry.size_bytes
        
        for key in keys_to_remove:
            self._remove_entry(key)
        
        # If still need space, remove LRU entries
        while (self._total_size_bytes + needed_bytes > self.max_memory_bytes or 
               len(self._cache) >= self.max_size) and self._cache:
            # Remove least recently used (first item)
            key, entry = self._cache.popitem(last=False)
            self._total_size_bytes -= entry.size_bytes
            evicted_bytes += entry.size_bytes
            self._evictions += 1
        
        return self._total_size_bytes + needed_bytes <= self.max_memory_bytes
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._total_size_bytes = 0
            gc.collect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "memory_usage_mb": self._total_size_bytes / 1024 / 1024,
                "max_memory_mb": self.max_memory_bytes / 1024 / 1024,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "evictions": self._evictions,
                "ttl_seconds": self.ttl_seconds
            }

class CompactStringPool:
    """String interning pool to reduce memory usage for repeated strings."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._pool: Dict[str, str] = {}
        self._access_order: List[str] = []
        self._lock = threading.Lock()
    
    def intern(self, string: str) -> str:
        """Intern string to reduce memory usage."""
        if not isinstance(string, str) or len(string) > 1000:  # Skip very long strings
            return string
        
        with self._lock:
            if string in self._pool:
                # Move to end of access order
                if string in self._access_order:
                    self._access_order.remove(string)
                self._access_order.append(string)
                return self._pool[string]
            
            # Add new string
            if len(self._pool) >= self.max_size:
                # Remove oldest
                if self._access_order:
                    oldest = self._access_order.pop(0)
                    self._pool.pop(oldest, None)
            
            # Intern the string
            interned = sys.intern(string)
            self._pool[string] = interned
            self._access_order.append(string)
            
            return interned
    
    def clear(self):
        """Clear the string pool."""
        with self._lock:
            self._pool.clear()
            self._access_order.clear()
            gc.collect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            total_size = sum(sys.getsizeof(s) for s in self._pool.keys())
            return {
                "size": len(self._pool),
                "max_size": self.max_size,
                "memory_usage_bytes": total_size
            }

class WeakValueCache:
    """Cache using weak references to allow garbage collection."""
    
    def __init__(self, cleanup_interval: int = 300):
        self._cache: Dict[str, weakref.ref] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = cleanup_interval
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from weak cache."""
        with self._lock:
            self._maybe_cleanup()
            
            if key not in self._cache:
                return None
            
            ref = self._cache[key]
            value = ref()
            
            if value is None:
                # Object was garbage collected
                del self._cache[key]
                return None
            
            return value
    
    def put(self, key: str, value: Any):
        """Put value in weak cache."""
        with self._lock:
            self._maybe_cleanup()
            
            def cleanup_callback(ref):
                with self._lock:
                    # Remove dead reference
                    for k, v in list(self._cache.items()):
                        if v is ref:
                            del self._cache[k]
                            break
            
            self._cache[key] = weakref.ref(value, cleanup_callback)
    
    def _maybe_cleanup(self):
        """Clean up dead references periodically."""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_dead_refs()
            self._last_cleanup = current_time
    
    def _cleanup_dead_refs(self):
        """Remove dead weak references."""
        dead_keys = []
        for key, ref in self._cache.items():
            if ref() is None:
                dead_keys.append(key)
        
        for key in dead_keys:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self._cleanup_dead_refs()
            return {
                "size": len(self._cache),
                "cleanup_interval": self._cleanup_interval
            }

class MemoryEfficientDataManager:
    """Central manager for memory-efficient data structures."""
    
    def __init__(self):
        # Main caches with different characteristics
        self.response_cache = MemoryEfficientLRUCache(
            max_size=50, max_memory_mb=20, ttl_seconds=1800  # 30 minutes
        )
        self.embedding_cache = MemoryEfficientLRUCache(
            max_size=100, max_memory_mb=15, ttl_seconds=3600  # 1 hour
        )
        self.session_cache = WeakValueCache(cleanup_interval=300)
        self.string_pool = CompactStringPool(max_size=500)
        
        self._lock = threading.Lock()
    
    def cache_response(self, key: str, response: Any) -> bool:
        """Cache API response."""
        return self.response_cache.put(key, response)
    
    def get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached API response."""
        return self.response_cache.get(key)
    
    def cache_embedding(self, key: str, embedding: Any) -> bool:
        """Cache embedding vector."""
        return self.embedding_cache.put(key, embedding)
    
    def get_cached_embedding(self, key: str) -> Optional[Any]:
        """Get cached embedding vector."""
        return self.embedding_cache.get(key)
    
    def intern_string(self, string: str) -> str:
        """Intern string to reduce memory usage."""
        return self.string_pool.intern(string)
    
    def clear_all_caches(self):
        """Clear all caches and force garbage collection."""
        with self._lock:
            self.response_cache.clear()
            self.embedding_cache.clear()
            self.session_cache.clear()
            self.string_pool.clear()
            gc.collect()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        with self._lock:
            return {
                "response_cache": self.response_cache.get_stats(),
                "embedding_cache": self.embedding_cache.get_stats(),
                "session_cache": self.session_cache.get_stats(),
                "string_pool": self.string_pool.get_stats(),
                "total_caches": 4
            }
    
    def optimize_memory(self):
        """Perform memory optimization across all caches."""
        with self._lock:
            # Clear least important cache first
            if self.response_cache._total_size_bytes > 10 * 1024 * 1024:  # 10MB
                logger.info("Clearing response cache for memory optimization")
                self.response_cache.clear()
            
            # Clean up weak references
            self.session_cache._cleanup_dead_refs()
            
            # Force garbage collection
            gc.collect()
            
            logger.info("Memory optimization completed")

# Global instance
_data_manager = None

def get_data_manager() -> MemoryEfficientDataManager:
    """Get the global data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = MemoryEfficientDataManager()
    return _data_manager

def clear_all_caches():
    """Clear all caches globally."""
    manager = get_data_manager()
    manager.clear_all_caches()

def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics."""
    manager = get_data_manager()
    return manager.get_memory_stats()

def optimize_memory():
    """Perform global memory optimization."""
    manager = get_data_manager()
    manager.optimize_memory()