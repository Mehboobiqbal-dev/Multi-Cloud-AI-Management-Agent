import importlib.util
import os
from typing import Callable, Dict
from tools import Tool, tool_registry

def load_plugin(plugin_path: str) -> str:
    """Loads a custom plugin from a Python file and registers its functions as tools."""
    if not os.path.exists(plugin_path):
        return f"Plugin file not found: {plugin_path}"
    
    spec = importlib.util.spec_from_file_location("custom_plugin", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    loaded_tools = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if callable(attr) and hasattr(attr, '__name__') and not attr_name.startswith('_'):
            tool_name = f"custom_{attr_name}"
            description = attr.__doc__ or f"Custom tool from {plugin_path}: {attr_name}"
            tool_registry.register(Tool(tool_name, description, attr))
            loaded_tools.append(tool_name)
    
    if loaded_tools:
        return f"Loaded custom plugins: {', '.join(loaded_tools)}"
    else:
        return "No callable functions found in the plugin file."