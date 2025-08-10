import importlib
import inspect
import os
import logging
from core.config import settings
from core.structured_logging import structured_logger, LogContext, operation_context
from core.circuit_breaker import circuit_breaker, CircuitBreakerConfig

class ToolManager:
    def __init__(self, tool_directory='backend', memory=None):
        self.tool_directory = tool_directory
        self.memory = memory
        self.available_tools = self._discover_tools()
        self.tool_dependencies = self._map_dependencies()

    def _map_dependencies(self):
        deps = {}
        for tool_name in self.available_tools:
            try:
                module = importlib.import_module(f'{self.tool_directory}.{tool_name}')
                deps[tool_name] = getattr(module, 'DEPENDS_ON', [])
            except ImportError:
                continue
        return deps

    def _execute_with_fallbacks(self, tool_name, function_name, *args, **kwargs):
        module = importlib.import_module(f'{self.tool_directory}.{tool_name}')
        func = getattr(module, function_name)
        return func(*args, **kwargs)

    @circuit_breaker(
        'tool_execution',
        CircuitBreakerConfig(
            failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
            recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
            expected_exception=Exception,
            name='tool_execution'
        )
    )
    def use_tool(self, tool_name, function_name, *args, **kwargs):
        """Execute a tool with enhanced resilience and structured logging."""
        tool_context = LogContext(
            metadata={
                'tool_name': tool_name,
                'function_name': function_name,
                'operation_type': 'tool_execution'
            }
        )
        
        # Check memory for known solutions first
        if self.memory:
            memory_key = f"tool:{tool_name}:{function_name}"
            cached_solution = self.memory.get(memory_key)
            if cached_solution:
                structured_logger.log_tool_execution(
                    f"Using cached solution for {tool_name}.{function_name}",
                    tool_context,
                    {"cache_hit": True}
                )
                return cached_solution

        # Execute normally if no cached solution
        with operation_context('use_tool', tool_context):
            try:
                # Implement retry logic for network operations
                max_retries = getattr(settings, 'MAX_RETRIES', 3)
                retry_delay = float(getattr(settings, 'INITIAL_RETRY_DELAY', 2.0))  # seconds
                max_retry_delay = float(getattr(settings, 'MAX_RETRY_DELAY', 60.0))
                
                # Default timeout for network tools
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = int(getattr(settings, 'NETWORK_TIMEOUT', 30))
                
                if any(network_term in function_name.lower() for network_term in 
                       ['request', 'fetch', 'download', 'upload', 'connect', 'http', 'api', 'search', 'browse']):
                    # This is likely a network operation, implement retry logic
                    for attempt in range(max_retries):
                        try:
                            structured_logger.log_tool_execution(
                                f"Executing network tool {tool_name}.{function_name} (attempt {attempt+1}/{max_retries})",
                                tool_context,
                                {"attempt": attempt+1, "is_network_operation": True}
                            )
                            result = self._execute_with_fallbacks(tool_name, function_name, *args, **kwargs)
                            break
                        except Exception as e:
                            error_msg = str(e)
                            # Check if it's a network-related error
                            is_network_error = any(msg in error_msg.lower() for msg in [
                                "failed to connect", "connection refused", "timeout", 
                                "socket", "network", "unreachable", "dns", "http error",
                                "certificate", "ssl", "proxy", "gateway"
                            ])
                            
                            if is_network_error and attempt < max_retries - 1:
                                structured_logger.log_tool_execution(
                                    f"Network error in {tool_name}.{function_name} (attempt {attempt+1}/{max_retries}): {error_msg}",
                                    tool_context,
                                    {"error": error_msg, "attempt": attempt+1, "is_network_error": True}
                                )
                                import time
                                time.sleep(retry_delay)
                                retry_delay = min(retry_delay * 2, max_retry_delay)  # Exponential backoff with cap
                                continue
                            else:
                                # Not a network error or last attempt
                                raise
                else:
                    # Not a network operation, execute normally
                    structured_logger.log_tool_execution(
                        f"Executing tool {tool_name}.{function_name}",
                        tool_context,
                        {"is_network_operation": False}
                    )
                    result = self._execute_with_fallbacks(tool_name, function_name, *args, **kwargs)
                
                # Store successful executions in memory
                if self.memory and not isinstance(result, Exception):
                    self.memory.add(f"tool:{tool_name}:{function_name}", {
                        'args': args,
                        'kwargs': kwargs,
                        'result': result
                    })
                
                structured_logger.log_tool_execution(
                    f"Tool {tool_name}.{function_name} executed successfully",
                    tool_context,
                    {"success": True}
                )
                return result
            except Exception as e:
                structured_logger.log_tool_execution(
                    f"Tool {tool_name}.{function_name} execution failed: {str(e)}",
                    tool_context,
                    {"error": str(e), "success": False}
                )
                return self._handle_tool_error(tool_name, function_name, e, args, kwargs)

    def _discover_tools(self):
        tools = {}
        loaded = set()
        
        def load_recursive(tool_name):
            if tool_name in loaded:
                return
            
            try:
                module = importlib.import_module(f'{self.tool_directory}.{tool_name}')
                functions = inspect.getmembers(module, inspect.isfunction)
                tool_functions = {name: func for name, func in functions if not name.startswith('_')}
                
                if tool_functions:
                    tools[tool_name] = tool_functions
                    loaded.add(tool_name)
                    
                    # Load dependencies
                    for dep in getattr(module, 'DEPENDS_ON', []):
                        if dep not in loaded:
                            load_recursive(dep)
            except Exception as e:
                structured_logger.log_tool_execution(
                    f"Tool loading failed for {tool_name}: {e}",
                    LogContext(metadata={'tool_name': tool_name, 'operation_type': 'tool_loading'}),
                    {"error": str(e)}
                )
        return tools

    def get_tools(self):
        return list(self.available_tools.keys())

    def get_tool_functions(self, tool_name):
        try:
            module = importlib.import_module(f'{self.tool_directory}.{tool_name}')
            functions = inspect.getmembers(module, inspect.isfunction)
            return {name: func for name, func in functions}
        except ImportError:
            return {}