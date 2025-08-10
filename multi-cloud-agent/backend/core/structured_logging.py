"""Structured logging enhancements for better observability.

Provides structured logging with context, performance monitoring,
and integration with the agent's self-learning capabilities.
"""

import json
import time
import threading
import traceback
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of events for structured logging."""
    OPERATION_START = "operation_start"
    OPERATION_END = "operation_end"
    OPERATION_ERROR = "operation_error"
    PERFORMANCE_METRIC = "performance_metric"
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY_ATTEMPT = "retry_attempt"
    MEMORY_UPDATE = "memory_update"
    TOOL_EXECUTION = "tool_execution"
    SELF_LEARNING = "self_learning"
    USER_INTERACTION = "user_interaction"


@dataclass
class LogContext:
    """Context information for structured logs."""
    operation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    retry_count: Optional[int] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StructuredLogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    event_type: str
    message: str
    context: LogContext
    extra_data: Optional[Dict[str, Any]] = None


class PerformanceMonitor:
    """Monitor performance metrics and slow operations."""
    
    def __init__(self):
        self.slow_operations: List[Dict[str, Any]] = []
        self.operation_stats: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
    
    def record_operation(self, operation_name: str, duration_ms: float, context: LogContext):
        """Record operation performance."""
        with self.lock:
            # Update statistics
            if operation_name not in self.operation_stats:
                self.operation_stats[operation_name] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'min_duration': float('inf'),
                    'max_duration': 0.0,
                    'avg_duration': 0.0
                }
            
            stats = self.operation_stats[operation_name]
            stats['count'] += 1
            stats['total_duration'] += duration_ms
            stats['min_duration'] = min(stats['min_duration'], duration_ms)
            stats['max_duration'] = max(stats['max_duration'], duration_ms)
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            
            # Check if operation is slow
            slow_threshold = getattr(settings, 'SLOW_OPERATION_THRESHOLD_MS', 5000)
            if duration_ms > slow_threshold:
                slow_op = {
                    'operation': operation_name,
                    'duration_ms': duration_ms,
                    'timestamp': datetime.utcnow().isoformat(),
                    'context': asdict(context)
                }
                self.slow_operations.append(slow_op)
                
                # Keep only recent slow operations
                if len(self.slow_operations) > 100:
                    self.slow_operations = self.slow_operations[-50:]
                
                # Log slow operation
                structured_logger.log_performance_issue(
                    f"Slow operation detected: {operation_name}",
                    duration_ms,
                    context
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self.lock:
            return {
                'operation_stats': dict(self.operation_stats),
                'slow_operations': list(self.slow_operations),
                'total_operations': sum(stats['count'] for stats in self.operation_stats.values())
            }
    
    def reset_stats(self):
        """Reset performance statistics."""
        with self.lock:
            self.operation_stats.clear()
            self.slow_operations.clear()


class StructuredLogger:
    """Enhanced structured logger with context and performance monitoring."""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.context_stack = threading.local()
        self.enabled = getattr(settings, 'ENABLE_PERFORMANCE_MONITORING', True)
    
    def _get_context_stack(self) -> List[LogContext]:
        """Get thread-local context stack."""
        if not hasattr(self.context_stack, 'stack'):
            self.context_stack.stack = []
        return self.context_stack.stack
    
    def _merge_context(self, context: Optional[LogContext] = None) -> LogContext:
        """Merge provided context with context stack."""
        stack = self._get_context_stack()
        merged = LogContext()
        
        # Merge from stack (bottom to top)
        for ctx in stack:
            for field, value in asdict(ctx).items():
                if value is not None:
                    setattr(merged, field, value)
        
        # Merge provided context
        if context:
            for field, value in asdict(context).items():
                if value is not None:
                    setattr(merged, field, value)
        
        return merged
    
    def _log_structured(self, level: LogLevel, event_type: EventType, message: str, 
                       context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log structured entry."""
        merged_context = self._merge_context(context)
        
        entry = StructuredLogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level.value,
            event_type=event_type.value,
            message=message,
            context=merged_context,
            extra_data=extra_data
        )
        
        # Convert to JSON for structured logging
        log_data = {
            'timestamp': entry.timestamp,
            'level': entry.level,
            'event_type': entry.event_type,
            'message': entry.message,
            **asdict(entry.context),
            **(entry.extra_data or {})
        }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Log using appropriate level
        log_message = json.dumps(log_data, default=str)
        
        if level == LogLevel.DEBUG:
            logger.debug(log_message)
        elif level == LogLevel.INFO:
            logger.info(log_message)
        elif level == LogLevel.WARNING:
            logger.warning(log_message)
        elif level == LogLevel.ERROR:
            logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            logger.critical(log_message)
    
    @contextmanager
    def operation_context(self, operation_name: str, context: Optional[LogContext] = None):
        """Context manager for operation logging with performance monitoring."""
        start_time = time.time()
        
        # Create context dict, avoiding operation_id conflicts
        context_dict = asdict(context) if context else {}
        if 'operation_id' not in context_dict or context_dict['operation_id'] is None:
            context_dict['operation_id'] = f"{operation_name}_{int(start_time * 1000)}"
        
        operation_context = LogContext(**context_dict)
        
        # Push context to stack
        stack = self._get_context_stack()
        stack.append(operation_context)
        
        try:
            self._log_structured(
                LogLevel.INFO,
                EventType.OPERATION_START,
                f"Starting operation: {operation_name}",
                operation_context
            )
            
            yield operation_context
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            operation_context.duration_ms = duration_ms
            
            self._log_structured(
                LogLevel.INFO,
                EventType.OPERATION_END,
                f"Completed operation: {operation_name}",
                operation_context
            )
            
            # Record performance if monitoring is enabled
            if self.enabled:
                self.performance_monitor.record_operation(operation_name, duration_ms, operation_context)
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            operation_context.duration_ms = duration_ms
            operation_context.error_type = type(e).__name__
            
            self._log_structured(
                LogLevel.ERROR,
                EventType.OPERATION_ERROR,
                f"Operation failed: {operation_name} - {str(e)}",
                operation_context,
                {'exception': traceback.format_exc()}
            )
            
            raise
        
        finally:
            # Pop context from stack
            if stack:
                stack.pop()
    
    def log_retry_attempt(self, operation: str, attempt: int, error: str, context: Optional[LogContext] = None):
        """Log retry attempt."""
        retry_context = LogContext(retry_count=attempt, **(asdict(context) if context else {}))
        self._log_structured(
            LogLevel.WARNING,
            EventType.RETRY_ATTEMPT,
            f"Retry attempt {attempt} for {operation}: {error}",
            retry_context
        )
    
    def log_circuit_breaker_event(self, breaker_name: str, state: str, context: Optional[LogContext] = None):
        """Log circuit breaker state change."""
        self._log_structured(
            LogLevel.WARNING,
            EventType.CIRCUIT_BREAKER,
            f"Circuit breaker '{breaker_name}' state: {state}",
            context,
            {'breaker_name': breaker_name, 'state': state}
        )
    
    def log_performance_issue(self, message: str, duration_ms: float, context: Optional[LogContext] = None):
        """Log performance issue."""
        context_dict = asdict(context) if context else {}
        context_dict['duration_ms'] = duration_ms
        perf_context = LogContext(**context_dict)
        self._log_structured(
            LogLevel.WARNING,
            EventType.PERFORMANCE_METRIC,
            message,
            perf_context
        )
    
    def log_tool_execution(self, tool_name: str, success: bool, duration_ms: float, 
                          context: Optional[LogContext] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log tool execution."""
        tool_context = LogContext(
            tool_name=tool_name,
            duration_ms=duration_ms,
            **(asdict(context) if context else {})
        )
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Tool '{tool_name}' {'succeeded' if success else 'failed'}"
        
        self._log_structured(level, EventType.TOOL_EXECUTION, message, tool_context, extra_data)
    
    def log_self_learning_event(self, event: str, context: Optional[LogContext] = None, 
                               extra_data: Optional[Dict[str, Any]] = None):
        """Log self-learning event."""
        self._log_structured(
            LogLevel.INFO,
            EventType.SELF_LEARNING,
            f"Self-learning: {event}",
            context,
            extra_data
        )
    
    def log_memory_update(self, update_type: str, context: Optional[LogContext] = None, 
                         extra_data: Optional[Dict[str, Any]] = None):
        """Log memory update."""
        self._log_structured(
            LogLevel.INFO,
            EventType.MEMORY_UPDATE,
            f"Memory update: {update_type}",
            context,
            extra_data
        )
    
    def log_error(self, message: str, context: Optional[LogContext] = None, 
                  extra_data: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log_structured(
            LogLevel.ERROR,
            EventType.OPERATION_ERROR,
            message,
            context,
            extra_data
        )
    
    def log_agent_action(self, message: str, context: Optional[LogContext] = None, 
                        extra_data: Optional[Dict[str, Any]] = None):
        """Log agent action."""
        self._log_structured(
            LogLevel.INFO,
            EventType.USER_INTERACTION,
            message,
            context,
            extra_data
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance monitoring statistics."""
        return self.performance_monitor.get_stats()
    
    def reset_performance_stats(self):
        """Reset performance monitoring statistics."""
        self.performance_monitor.reset_stats()


# Global structured logger instance
structured_logger = StructuredLogger()


def operation_context(operation_name: str, context: Optional[LogContext] = None):
    """Decorator/context manager for operation logging.
    
    Can be used as a decorator or context manager:
    
    @operation_context('my_operation')
    def my_function():
        pass
    
    # Or as context manager:
    with operation_context('my_operation'):
        # do work
        pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with structured_logger.operation_context(operation_name, context):
                return func(*args, **kwargs)
        return wrapper
    
    # If called with function, act as decorator
    if callable(operation_name):
        func = operation_name
        operation_name = func.__name__
        return decorator(func)
    
    # Otherwise, return context manager
    return structured_logger.operation_context(operation_name, context)