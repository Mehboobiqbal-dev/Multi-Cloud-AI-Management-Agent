"""Circuit breaker implementation for resilient operations.

Provides circuit breaker functionality to prevent cascading failures
by temporarily disabling operations that are likely to fail.
"""

import time
import threading
from typing import Any, Callable, Dict, Optional, Type
from enum import Enum
from dataclasses import dataclass
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open" # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    name: str = "default"


class CircuitBreaker:
    """Circuit breaker implementation.
    
    Monitors failures and opens the circuit when failure threshold is exceeded.
    After recovery timeout, allows test calls to check if service has recovered.
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.lock = threading.RLock()
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker."""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.config.name}' transitioning to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.config.name}' is OPEN"
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.config.expected_exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info(f"Circuit breaker '{self.config.name}' reset to CLOSED")
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.config.name}' opened after {self.failure_count} failures"
            )
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = 0.0
            logger.info(f"Circuit breaker '{self.config.name}' manually reset")
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state == CircuitState.CLOSED


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.RLock()
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self.lock:
            if name not in self.breakers:
                if config is None:
                    # Use default config from settings
                    config = CircuitBreakerConfig(
                        failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
                        recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
                        expected_exception=getattr(settings, 'CIRCUIT_BREAKER_EXPECTED_EXCEPTION', Exception),
                        name=name
                    )
                else:
                    config.name = name
                
                self.breakers[name] = CircuitBreaker(config)
                logger.info(f"Created circuit breaker '{name}'")
            
            return self.breakers[name]
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        with self.lock:
            return {
                name: {
                    'state': breaker.state.value,
                    'failure_count': breaker.failure_count,
                    'last_failure_time': breaker.last_failure_time,
                    'is_open': breaker.is_open,
                    'is_closed': breaker.is_closed
                }
                for name, breaker in self.breakers.items()
            }


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator to add circuit breaker protection to functions.
    
    Args:
        name: Name of the circuit breaker
        config: Optional configuration (uses defaults from settings if not provided)
    
    Example:
        @circuit_breaker('api_calls')
        def call_external_api():
            # This function will be protected by a circuit breaker
            pass
    """
    def decorator(func: Callable) -> Callable:
        breaker = circuit_manager.get_breaker(name, config)
        return breaker(func)
    return decorator


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get a circuit breaker instance.
    
    Args:
        name: Name of the circuit breaker
        config: Optional configuration
    
    Returns:
        CircuitBreaker instance
    """
    return circuit_manager.get_breaker(name, config)