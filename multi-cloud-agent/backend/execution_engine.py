import logging
from typing import Dict, Any, Tuple
import requests
from tool_manager import ToolManager

logging.basicConfig(level=logging.INFO)

def execute_step(step: Dict[str, Any], kb: 'KnowledgeBase', tool_manager: 'ToolManager') -> Tuple[Any, Any]:
    """Executes a single step and returns the result and any errors."""
    action = step.get("action")
    params = step.get("params", {})

    logging.info(f"Executing action: {action} with params: {params}")

    try:
        if action == "search_web":
            query = params.get("query")
            if not query:
                return None, "Missing 'query' parameter for 'search_web' action."
            
            # Use the web_search tool
            try:
                search_results = tool_manager.use_tool("web_search", "search", query=query)
                return search_results, None
            except Exception as e:
                return None, f"Web search tool failed: {str(e)}"

        elif action == "ask_user":
            return params.get('question'), None

        elif action == "finish_task":
            return params.get('summary'), None

        elif action == "learn":
            key = params.get("key")
            value = params.get("value")
            if not key or not value:
                return None, "Missing 'key' or 'value' for 'learn' action."
            kb.add(key, value)
            return f"Learned: {key}", None

        elif action == "use_tool":
            tool_name = params.get("tool_name")
            function_name = params.get("function_name")
            args = params.get("args", [])
            kwargs = params.get("kwargs", {})
            if not tool_name or not function_name:
                return None, "Missing 'tool_name' or 'function_name' for 'use_tool' action."
            return tool_manager.use_tool(tool_name, function_name, *args, **kwargs), None

        else:
            return None, f"Unknown action: {action}"

    except Exception as e:
        return None, str(e)