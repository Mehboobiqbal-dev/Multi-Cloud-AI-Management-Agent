from typing import Dict, Any, Callable, List
from cloud_handlers import handle_clouds

class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
        }

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self._tools.get(name)

    def get_all_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_all_tools_dict(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self.get_all_tools()]

# --- Core Tools ---

def search_web(query: str) -> str:
    """Searches the web for the given query."""
    # This is a placeholder. In a real implementation, this would use a search engine API.
    return f"Search results for '{query}'"

def read_file(path: str) -> str:
    """Reads the contents of a file."""
    with open(path, "r") as f:
        return f.read()

def write_file(path: str, content: str):
    """Writes content to a file."""
    try:
        with open(path, "w") as f:
            f.write(content)
    except Exception as e:
        raise Exception(f"Failed to write to file: {e}")

def execute_command(command: str) -> str:
    """Executes a shell command."""
    # This is a placeholder. In a real implementation, this would use subprocess.run.
    return f"Executed command: {command}"

def cloud_operation(cloud: str, operation: str, resource: str, params: Dict[str, Any], user_creds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a cloud operation.
    :param cloud: The cloud provider (aws, azure, gcp).
    :param operation: The operation to perform (create, delete, list).
    :param resource: The resource to operate on (vm, storage).
    :param params: A dictionary of parameters for the operation.
    :param user_creds: A dictionary of user credentials for the cloud provider.
    """
    return handle_clouds([{"cloud": cloud, "operation": operation, "resource": resource, "params": params}], user_creds)

def user_interaction(message: str) -> str:
    """
    Sends a message to the user.
    :param message: The message to send to the user.
    """
    return message

# --- Tool Registration ---

tool_registry = ToolRegistry()
tool_registry.register(Tool("search_web", "Searches the web for a given query.", search_web))
tool_registry.register(Tool("read_file", "Reads the contents of a file.", read_file))
tool_registry.register(Tool("write_file", "Writes content to a file.", write_file))
tool_registry.register(Tool("execute_command", "Executes a shell command.", execute_command))
tool_registry.register(Tool("cloud_operation", "Executes a cloud operation.", cloud_operation))
tool_registry.register(Tool("user_interaction", "Sends a message to the user.", user_interaction))
