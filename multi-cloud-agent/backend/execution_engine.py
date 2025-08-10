import logging
from typing import Dict, Any, Tuple
import requests
from tool_manager import ToolManager
from tools import search_web as registered_search_web
from core.config import settings

logging.basicConfig(level=logging.INFO)

def execute_step(step: Dict[str, Any], kb: 'KnowledgeBase', tool_manager: 'ToolManager') -> Tuple[Any, Any]:
    """Executes a single step and returns the result and any errors."""
    action = step.get("action")
    params = step.get("params", {})
    
    logging.info(f"Executing action: {action} with params: {params}")
    
    # Define max retries for network-dependent actions
    max_retries = getattr(settings, "MAX_RETRIES", 3)
    network_dependent_actions = ["search_web", "use_tool"]
    
    try:
        # For network-dependent actions, implement retry logic
        if action in network_dependent_actions:
            retry_count = 0
            # Use float for finer control over backoff
            retry_delay = float(getattr(settings, "INITIAL_RETRY_DELAY", 2.0))  # Initial delay in seconds
            last_error = None
            
            while retry_count < max_retries:
                try:
                    if action == "search_web":
                        query = params.get("query")
                        if not query:
                            return None, "Missing 'query' parameter for 'search_web' action."
                        engine = params.get("engine", "duckduckgo")
                        
                        # Use the unified search_web tool registered in tools.py (browsing-backed)
                        search_results = registered_search_web(query=query, engine=engine)
                        return search_results, None
                    
                    elif action == "use_tool":
                        tool_name = params.get("tool_name")
                        function_name = params.get("function_name")
                        args = params.get("args", [])
                        kwargs = params.get("kwargs", {})
                        
                        # Add timeout for network-related tools
                        if "timeout" not in kwargs and tool_name in ["http_request", "api_call", "fetch_url"]:
                            kwargs["timeout"] = int(getattr(settings, "NETWORK_TIMEOUT", 30))  # configurable timeout
                            
                        if not tool_name or not function_name:
                            return None, "Missing 'tool_name' or 'function_name' for 'use_tool' action."
                        return tool_manager.use_tool(tool_name, function_name, *args, **kwargs), None
                
                except Exception as e:
                    error_msg = str(e)
                    last_error = e
                    
                    # Check if it's a network-related error
                    is_network_error = any(msg in error_msg.lower() for msg in [
                        "failed to connect", "connection refused", "timeout", 
                        "socket", "network", "unreachable", "dns", "http error",
                        "certificate", "ssl", "proxy", "gateway"
                    ])
                    
                    if is_network_error:
                        retry_count += 1
                        if retry_count < max_retries:
                            import time
                            logging.warning(f"Network error executing {action}. Retrying in {retry_delay}s... ({retry_count}/{max_retries})")
                            time.sleep(retry_delay)
                            # Exponential backoff with cap
                            retry_delay = min(retry_delay * 2, float(getattr(settings, "MAX_RETRY_DELAY", 60.0)))
                        else:
                            # Max retries reached
                            return None, f"Network error after {max_retries} attempts: {error_msg}"
                    else:
                        # Not a network error, don't retry
                        return None, f"Error executing {action}: {error_msg}"
            
            # If we exited the loop due to max retries
            if retry_count == max_retries:
                return None, f"Failed after {max_retries} attempts: {str(last_error)}"
        
        # For non-network-dependent actions, execute normally
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

        else:
            return None, f"Unknown action: {action}"

    except Exception as e:
        return None, str(e)