import importlib
import inspect
import os

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
                print(f"Tool loading failed for {tool_name}: {e}")
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

    def use_tool(self, tool_name, function_name, *args, **kwargs):
        # Check memory for known solutions first
        if self.memory:
            memory_key = f"tool:{tool_name}:{function_name}"
            cached_solution = self.memory.get(memory_key)
            if cached_solution:
                return cached_solution

        # Execute normally if no cached solution
        try:
            result = self._execute_with_fallbacks(tool_name, function_name, *args, **kwargs)
            
            # Store successful executions in memory
            if self.memory and not isinstance(result, Exception):
                self.memory.add(f"tool:{tool_name}:{function_name}", {
                    'args': args,
                    'kwargs': kwargs,
                    'result': result
                })
            return result
        except Exception as e:
            return self._handle_tool_error(tool_name, function_name, e, args, kwargs)