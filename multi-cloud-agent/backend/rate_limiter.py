import time
import threading
import random
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logging.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        with self.lock:
            self.failure_count = 0
            self.state = "CLOSED"
    
    def _on_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logging.warning(f"Circuit breaker opened after {self.failure_count} failures")

class RateLimiter:
    """
    Enhanced rate limiter with exponential backoff and circuit breaker.
    Implements a sliding window rate limiter with intelligent retry logic.
    """
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.circuit_breakers: Dict[str, CircuitBreaker] = defaultdict(lambda: CircuitBreaker())
        self.lock = threading.Lock()
        self.backoff_multipliers: Dict[str, float] = defaultdict(lambda: 1.0)
        self.last_429_time: Dict[str, float] = defaultdict(lambda: 0)
        
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
        Wait if rate limit would be exceeded with exponential backoff.
        
        Returns:
            None if no wait needed, otherwise the wait time in seconds
        """
        if not self.is_allowed(key, max_requests, window_seconds):
            # Calculate wait time until oldest request expires
            with self.lock:
                if self.requests[key]:
                    oldest_request = self.requests[key][0]
                    base_wait_time = window_seconds - (time.time() - oldest_request) + 1
                    
                    # Apply exponential backoff for 429 errors
                    backoff_multiplier = self.backoff_multipliers[key]
                    wait_time = base_wait_time * backoff_multiplier
                    
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0.8, 1.2)
                    wait_time *= jitter
                    
                    if wait_time > 0:
                        logging.info(f"Rate limit hit for {key}. Waiting {wait_time:.1f} seconds (backoff: {backoff_multiplier:.2f}x)")
                        time.sleep(wait_time)
                        return wait_time
        return None
    
    def handle_429_error(self, key: str, retry_after: Optional[int] = None):
        """
        Handle 429 error by updating backoff multiplier and circuit breaker.
        """
        current_time = time.time()
        self.last_429_time[key] = current_time
        
        # Increase backoff multiplier
        self.backoff_multipliers[key] = min(self.backoff_multipliers[key] * 1.5, 10.0)
        
        # Update circuit breaker
        self.circuit_breakers[key]._on_failure()
        
        if retry_after:
            logging.warning(f"429 error for {key}, retry after {retry_after}s, backoff: {self.backoff_multipliers[key]:.2f}x")
        else:
            logging.warning(f"429 error for {key}, backoff: {self.backoff_multipliers[key]:.2f}x")
    
    def handle_success(self, key: str):
        """
        Handle successful request by resetting backoff multiplier.
        """
        self.backoff_multipliers[key] = max(self.backoff_multipliers[key] * 0.8, 1.0)
        self.circuit_breakers[key]._on_success()
    
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
    
    def get_circuit_breaker_status(self, key: str) -> Dict[str, any]:
        """
        Get circuit breaker status for monitoring.
        """
        cb = self.circuit_breakers[key]
        return {
            "state": cb.state,
            "failure_count": cb.failure_count,
            "last_failure_time": cb.last_failure_time,
            "backoff_multiplier": self.backoff_multipliers[key],
            "last_429_time": self.last_429_time[key]
        }
    
    def reset_circuit_breaker(self, key: str):
        """
        Reset circuit breaker for a specific key.
        """
        self.circuit_breakers[key] = CircuitBreaker()
        self.backoff_multipliers[key] = 1.0
        self.last_429_time[key] = 0
        logging.info(f"Reset circuit breaker for {key}")

# Global rate limiter instance
rate_limiter = RateLimiter()

def with_rate_limit(provider: str, max_requests: int = 50, window_seconds: int = 60):
    """
    Enhanced decorator to add rate limiting to API calls with circuit breaker.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check circuit breaker first
            cb = rate_limiter.circuit_breakers[provider]
            if cb.state == "OPEN":
                if time.time() - cb.last_failure_time > cb.recovery_timeout:
                    cb.state = "HALF_OPEN"
                    logging.info(f"Circuit breaker for {provider} transitioning to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker for {provider} is OPEN")
            
            # Wait if rate limit would be exceeded
            wait_time = rate_limiter.wait_if_needed(provider, max_requests, window_seconds)
            if wait_time:
                logging.info(f"Rate limited {provider} for {wait_time:.1f}s")
            
            try:
                result = func(*args, **kwargs)
                rate_limiter.handle_success(provider)
                return result
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    rate_limiter.handle_429_error(provider)
                raise e
        return wrapper
    return decorator