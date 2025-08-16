import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional
import logging

class RateLimiter:
    """
    Simple rate limiter to prevent API quota exhaustion.
    Implements a sliding window rate limiter.
    """
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
        
    def is_allowed(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """
        Check if a request is allowed based on rate limits.
        
        Args:
            key: Identifier for the rate limit (e.g., 'gemini', 'groq')
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        with self.lock:
            # Clean old requests outside the window
            while (self.requests[key] and 
                   current_time - self.requests[key][0] > window_seconds):
                self.requests[key].popleft()
            
            # Check if we're under the limit
            if len(self.requests[key]) < max_requests:
                self.requests[key].append(current_time)
                return True
            
            return False
    
    def wait_if_needed(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> Optional[float]:
        """
        Wait if rate limit would be exceeded.
        
        Returns:
            None if no wait needed, otherwise the wait time in seconds
        """
        if not self.is_allowed(key, max_requests, window_seconds):
            # Calculate wait time until oldest request expires
            with self.lock:
                if self.requests[key]:
                    oldest_request = self.requests[key][0]
                    wait_time = window_seconds - (time.time() - oldest_request) + 1
                    if wait_time > 0:
                        logging.info(f"Rate limit hit for {key}. Waiting {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                        return wait_time
        return None
    
    def get_remaining_requests(self, key: str, max_requests: int = 60, window_seconds: int = 60) -> int:
        """
        Get the number of remaining requests in the current window.
        """
        current_time = time.time()
        
        with self.lock:
            # Clean old requests
            while (self.requests[key] and 
                   current_time - self.requests[key][0] > window_seconds):
                self.requests[key].popleft()
            
            return max_requests - len(self.requests[key])

# Global rate limiter instance
rate_limiter = RateLimiter()

def with_rate_limit(provider: str, max_requests: int = 50, window_seconds: int = 60):
    """
    Decorator to add rate limiting to API calls.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Wait if rate limit would be exceeded
            wait_time = rate_limiter.wait_if_needed(provider, max_requests, window_seconds)
            if wait_time:
                logging.info(f"Rate limited {provider} for {wait_time:.1f}s")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator