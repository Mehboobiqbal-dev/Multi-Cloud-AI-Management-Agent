"""Real-time memory monitoring and automatic optimization for 512MB limit.

This module provides continuous memory monitoring and automatic interventions
when memory usage approaches the 512MB limit on Render.com.
"""

import os
import gc
import sys
import time
import psutil
import logging
import threading
from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MemoryThreshold:
    """Memory threshold configuration."""
    name: str
    threshold_mb: float
    threshold_percent: float
    action: Callable[[], None]
    cooldown_seconds: int = 30
    last_triggered: datetime = None

class MemoryMonitor:
    """Real-time memory monitor with automatic optimization."""
    
    def __init__(self, memory_limit_mb: int = 512):
        self.memory_limit_mb = memory_limit_mb
        self.monitoring = False
        self.monitor_thread = None
        self.check_interval = 10  # seconds
        self.memory_history = []
        self.max_history_size = 100
        
        # Define memory thresholds and actions
        self.thresholds = [
            MemoryThreshold(
                name="warning",
                threshold_mb=350,  # 68% of 512MB
                threshold_percent=68.0,
                action=self._warning_action,
                cooldown_seconds=60
            ),
            MemoryThreshold(
                name="aggressive_gc",
                threshold_mb=400,  # 78% of 512MB
                threshold_percent=78.0,
                action=self._aggressive_gc_action,
                cooldown_seconds=30
            ),
            MemoryThreshold(
                name="emergency",
                threshold_mb=450,  # 88% of 512MB
                threshold_percent=88.0,
                action=self._emergency_action,
                cooldown_seconds=15
            ),
            MemoryThreshold(
                name="critical",
                threshold_mb=480,  # 94% of 512MB
                threshold_percent=94.0,
                action=self._critical_action,
                cooldown_seconds=5
            )
        ]
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": memory_percent,
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {"error": str(e), "timestamp": datetime.now()}
    
    def _warning_action(self):
        """Warning level action - log and light cleanup."""
        logger.warning(f"Memory usage approaching limit (68% of {self.memory_limit_mb}MB)")
        gc.collect()
    
    def _aggressive_gc_action(self):
        """Aggressive garbage collection action."""
        logger.warning(f"Memory usage high (78% of {self.memory_limit_mb}MB) - performing aggressive GC")
        
        # Multiple rounds of garbage collection
        collected_total = 0
        for generation in range(3):
            collected = gc.collect(generation)
            collected_total += collected
        
        # Additional cleanup
        gc.collect()
        
        logger.info(f"Aggressive GC collected {collected_total} objects")
    
    def _emergency_action(self):
        """Emergency action - clear caches and force cleanup."""
        logger.error(f"Memory usage critical (88% of {self.memory_limit_mb}MB) - emergency cleanup")
        
        # Clear memory-efficient caches first
        try:
            from core.memory_efficient_cache import optimize_memory
            optimize_memory()
            logger.info("Cleared memory-efficient caches")
        except Exception as e:
            logger.debug(f"Failed to clear efficient caches: {e}")
        
        # Clear all possible caches
        self._clear_caches()
        
        # Force garbage collection
        self._aggressive_gc_action()
        
        # Try to free up system memory
        try:
            if hasattr(os, 'sync'):
                os.sync()
        except Exception as e:
            logger.debug(f"Failed to sync: {e}")
    
    def _critical_action(self):
        """Critical action - last resort cleanup."""
        logger.critical(f"Memory usage extremely critical (94% of {self.memory_limit_mb}MB) - last resort cleanup")
        
        # Emergency cleanup
        self._emergency_action()
        
        # Clear import caches
        sys.modules.clear()
        
        # Force Python to release memory back to OS
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.malloc_trim(0)
        except Exception as e:
            logger.debug(f"Failed to trim malloc: {e}")
    
    def _clear_caches(self):
        """Clear various Python caches."""
        try:
            # Clear function caches
            import functools
            if hasattr(functools, '_CacheInfo'):
                # Clear lru_cache caches
                pass
            
            # Clear regex cache
            import re
            re.purge()
            
            # Clear linecache
            import linecache
            linecache.clearcache()
            
            # Clear import cache
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            
            logger.debug("Cleared Python caches")
            
        except Exception as e:
            logger.debug(f"Failed to clear some caches: {e}")
    
    def _check_thresholds(self, memory_info: Dict[str, Any]):
        """Check memory thresholds and trigger actions."""
        current_mb = memory_info.get('rss_mb', 0)
        current_time = datetime.now()
        
        for threshold in self.thresholds:
            if current_mb >= threshold.threshold_mb:
                # Check cooldown
                if (threshold.last_triggered is None or 
                    current_time - threshold.last_triggered >= timedelta(seconds=threshold.cooldown_seconds)):
                    
                    try:
                        threshold.action()
                        threshold.last_triggered = current_time
                        logger.info(f"Triggered {threshold.name} action at {current_mb:.1f}MB")
                    except Exception as e:
                        logger.error(f"Failed to execute {threshold.name} action: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info(f"Starting memory monitor for {self.memory_limit_mb}MB limit")
        
        while self.monitoring:
            try:
                memory_info = self.get_memory_info()
                
                # Add to history
                self.memory_history.append(memory_info)
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)
                
                # Check thresholds
                self._check_thresholds(memory_info)
                
                # Log periodic status
                current_mb = memory_info.get('rss_mb', 0)
                if len(self.memory_history) % 6 == 0:  # Every minute with 10s interval
                    logger.debug(f"Memory status: {current_mb:.1f}MB / {self.memory_limit_mb}MB ({current_mb/self.memory_limit_mb*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"Error in memory monitor loop: {e}")
            
            time.sleep(self.check_interval)
    
    def start_monitoring(self):
        """Start the memory monitoring thread."""
        if self.monitoring:
            logger.warning("Memory monitoring already started")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop the memory monitoring thread."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Memory monitoring stopped")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics and history."""
        if not self.memory_history:
            return {"error": "No memory history available"}
        
        recent_memory = [info.get('rss_mb', 0) for info in self.memory_history[-10:]]
        
        return {
            "current_mb": self.memory_history[-1].get('rss_mb', 0),
            "limit_mb": self.memory_limit_mb,
            "usage_percent": (self.memory_history[-1].get('rss_mb', 0) / self.memory_limit_mb) * 100,
            "average_mb_last_10": sum(recent_memory) / len(recent_memory) if recent_memory else 0,
            "peak_mb": max(info.get('rss_mb', 0) for info in self.memory_history),
            "history_size": len(self.memory_history),
            "monitoring_active": self.monitoring
        }

# Global memory monitor instance
_memory_monitor = None

def get_memory_monitor() -> MemoryMonitor:
    """Get the global memory monitor instance."""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor

def start_memory_monitoring():
    """Start global memory monitoring."""
    monitor = get_memory_monitor()
    monitor.start_monitoring()

def stop_memory_monitoring():
    """Stop global memory monitoring."""
    monitor = get_memory_monitor()
    monitor.stop_monitoring()

def get_memory_stats() -> Dict[str, Any]:
    """Get current memory statistics."""
    monitor = get_memory_monitor()
    return monitor.get_memory_stats()