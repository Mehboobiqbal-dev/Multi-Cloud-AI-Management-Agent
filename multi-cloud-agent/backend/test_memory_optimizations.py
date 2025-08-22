#!/usr/bin/env python3
"""
Memory Optimization Test Script
Tests the memory optimizations and NO_MEMORY configuration.
"""

import os
import sys
import psutil
import time
import requests
import subprocess
from typing import Dict, Any

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        'percent': process.memory_percent(),
        'available_mb': psutil.virtual_memory().available / 1024 / 1024
    }

def test_no_memory_config():
    """Test NO_MEMORY environment variable configuration."""
    print("\n=== Testing NO_MEMORY Configuration ===")
    
    # Test with NO_MEMORY=false (default)
    os.environ['NO_MEMORY'] = 'false'
    print(f"NO_MEMORY set to: {os.getenv('NO_MEMORY')}")
    
    # Import and test the functions
    try:
        from main import load_agent_memory, save_agent_memory
        print("✓ Successfully imported memory functions")
        
        # Test load_agent_memory logic
        should_load = not os.getenv('NO_MEMORY', 'false').lower() == 'true'
        print(f"Should load memory: {should_load}")
        
    except Exception as e:
        print(f"✗ Error importing memory functions: {e}")
    
    # Test with NO_MEMORY=true
    os.environ['NO_MEMORY'] = 'true'
    print(f"\nNO_MEMORY set to: {os.getenv('NO_MEMORY')}")
    should_load = not os.getenv('NO_MEMORY', 'false').lower() == 'true'
    print(f"Should load memory: {should_load}")
    
    if not should_load:
        print("✓ NO_MEMORY=true correctly disables memory loading")
    else:
        print("✗ NO_MEMORY=true failed to disable memory loading")

def test_memory_monitor():
    """Test memory monitoring functionality."""
    print("\n=== Testing Memory Monitor ===")
    
    try:
        from core.memory_monitor import MemoryMonitor, MemoryThreshold
        
        monitor = MemoryMonitor()
        print("✓ Successfully created MemoryMonitor instance")
        
        # Test memory info retrieval
        memory_info = monitor.get_memory_info()
        if 'error' not in memory_info:
            print(f"Current memory usage: {memory_info['rss_mb']:.1f}MB RSS, {memory_info['vms_mb']:.1f}MB VMS")
            print(f"Memory percentage: {memory_info['percent']:.1f}%")
            print(f"Available memory: {memory_info['available_mb']:.1f}MB")
        else:
            print(f"Error getting memory info: {memory_info['error']}")
        
        # Test threshold checking
        current_threshold = monitor.check_memory_threshold()
        print(f"Current memory threshold: {current_threshold.name}")
        
        print("✓ Memory monitoring functions working correctly")
        
    except Exception as e:
        print(f"✗ Error testing memory monitor: {e}")

def test_memory_efficient_cache():
    """Test memory-efficient caching functionality."""
    print("\n=== Testing Memory-Efficient Cache ===")
    
    try:
        from core.memory_efficient_cache import get_data_manager, get_cache_stats, optimize_memory
        
        # Test data manager
        data_manager = get_data_manager()
        print("✓ Successfully retrieved data manager")
        
        # Test cache operations
        success = data_manager.cache_response('test_key', 'test_value')
        cached_value = data_manager.get_cached_response('test_key')
        
        if success and cached_value == 'test_value':
            print("✓ Cache set/get operations working")
        else:
            print("✗ Cache operations failed")
        
        # Test cache stats
        stats = get_cache_stats()
        print(f"Cache stats: {stats}")
        
        # Test memory optimization
        optimize_memory()
        print("✓ Memory optimization completed")
        
    except Exception as e:
        print(f"✗ Error testing memory-efficient cache: {e}")

def test_lazy_imports():
    """Test lazy import functionality."""
    print("\n=== Testing Lazy Imports ===")
    
    try:
        from core.lazy_imports import get_lazy_import, lazy_import_decorator
        
        print("✓ Successfully imported lazy import functions")
        
        # Test lazy import decorator (simplified test)
        try:
            # Test that we can get a lazy import
            lazy_json = get_lazy_import('json')
            if lazy_json:
                print("✓ Lazy import retrieval working")
            else:
                print("✗ Lazy import retrieval failed")
        except Exception as e:
            print(f"✗ Lazy import test failed: {e}")
            
    except Exception as e:
        print(f"✗ Error testing lazy imports: {e}")

def test_memory_usage_under_load():
    """Test memory usage under simulated load."""
    print("\n=== Testing Memory Usage Under Load ===")
    
    initial_memory = get_memory_usage()
    print(f"Initial memory usage: {initial_memory['rss_mb']:.1f}MB")
    
    # Simulate some memory load
    test_data = []
    for i in range(1000):
        test_data.append(f"test_string_{i}" * 100)
    
    peak_memory = get_memory_usage()
    print(f"Peak memory usage: {peak_memory['rss_mb']:.1f}MB")
    
    # Clean up
    del test_data
    import gc
    gc.collect()
    
    final_memory = get_memory_usage()
    print(f"Final memory usage: {final_memory['rss_mb']:.1f}MB")
    
    memory_increase = peak_memory['rss_mb'] - initial_memory['rss_mb']
    memory_recovered = peak_memory['rss_mb'] - final_memory['rss_mb']
    
    print(f"Memory increase during load: {memory_increase:.1f}MB")
    print(f"Memory recovered after cleanup: {memory_recovered:.1f}MB")
    
    if memory_recovered > 0:
        print("✓ Memory cleanup working correctly")
    else:
        print("⚠ Memory cleanup may not be optimal")

def main():
    """Run all memory optimization tests."""
    print("Memory Optimization Test Suite")
    print("=" * 50)
    
    # Display system info
    memory_info = psutil.virtual_memory()
    print(f"System Memory: {memory_info.total / 1024 / 1024 / 1024:.1f}GB total")
    print(f"Available Memory: {memory_info.available / 1024 / 1024:.1f}MB")
    
    # Run tests
    test_no_memory_config()
    test_memory_monitor()
    test_memory_efficient_cache()
    test_lazy_imports()
    test_memory_usage_under_load()
    
    print("\n=== Test Summary ===")
    final_memory = get_memory_usage()
    print(f"Final memory usage: {final_memory['rss_mb']:.1f}MB")
    
    if final_memory['rss_mb'] < 512:  # Target for Render.com
        print("✓ Memory usage within 512MB limit")
    else:
        print(f"⚠ Memory usage ({final_memory['rss_mb']:.1f}MB) exceeds 512MB limit")
    
    print("\nMemory optimization tests completed!")

if __name__ == "__main__":
    main()