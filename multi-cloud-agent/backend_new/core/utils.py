import json
import uuid
import re
import time
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Callable
import logging

# Configure logger
logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """
    Generate a random UUID string.
    """
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """
    Get current UTC timestamp in ISO format.
    """
    return datetime.now(timezone.utc).isoformat()

def parse_json(json_str: str) -> Dict[str, Any]:
    """
    Safely parse a JSON string.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed JSON as a dictionary
        
    Raises:
        ValueError: If the JSON string is invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON: {e}")

def to_json(data: Any) -> str:
    """
    Convert data to a JSON string.
    
    Args:
        data: Data to convert to JSON
        
    Returns:
        JSON string representation of the data
    """
    try:
        return json.dumps(data, default=str)
    except TypeError as e:
        logger.error(f"Failed to convert to JSON: {e}")
        raise ValueError(f"Cannot convert to JSON: {e}")

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    # Remove any script tags
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_str, flags=re.DOTALL)
    
    # Remove any HTML tags
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    
    # Remove any SQL injection patterns
    sanitized = re.sub(r'[\\\'\";]', '', sanitized)
    
    return sanitized

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Retry decorator for functions that might fail temporarily.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"All {max_attempts} retry attempts failed for {func.__name__}: {e}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} for {func.__name__} failed: {e}. "
                        f"Retrying in {current_delay:.2f} seconds..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    attempt += 1
        
        return wrapper
    
    return decorator

def hash_data(data: Union[str, bytes, Dict, List]) -> str:
    """
    Create a SHA-256 hash of the provided data.
    
    Args:
        data: Data to hash (string, bytes, or JSON-serializable object)
        
    Returns:
        Hexadecimal string representation of the hash
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True)
    
    if isinstance(data, str):
        data = data.encode()
        
    return hashlib.sha256(data).hexdigest()

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, adding a suffix if truncated.
    
    Args:
        text: String to truncate
        max_length: Maximum length of the string
        suffix: Suffix to add if the string is truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_error_response(error: Exception) -> Dict[str, Any]:
    """
    Format an exception into a standardized error response.
    
    Args:
        error: Exception to format
        
    Returns:
        Dictionary with error details
    """
    return {
        "status": "error",
        "message": str(error),
        "error_type": error.__class__.__name__,
        "timestamp": get_timestamp()
    }