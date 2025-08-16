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


def parse_json_tolerant(response_text: str) -> Dict[str, Any]:
    """
    Tolerant JSON parser that can handle malformed JSON from LLM responses.
    
    This function implements comprehensive cleaning and extraction logic to handle:
    - JSON blocks wrapped in ```json``` 
    - Backticks around URLs and other values
    - Invalid control characters
    - Comments and other non-JSON content
    - Unescaped newlines
    - Whitespace issues
    
    Args:
        response_text: Raw text response that may contain JSON
        
    Returns:
        Parsed JSON as a dictionary
        
    Raises:
        ValueError: If no valid JSON can be extracted and parsed
    """
    if not response_text or not response_text.strip():
        raise ValueError("Empty response text")
    
    # Try to find ```json``` block first
    json_match = re.search(r'```json\n([\s\S]*?)\n```', response_text)
    if json_match:
        json_string = json_match.group(1)
    else:
        # Fallback: try to find any JSON object with proper nesting
        json_matches = []
        
        # Find all potential JSON starts
        start_positions = [m.start() for m in re.finditer(r'\{', response_text)]
        
        for start_pos in start_positions:
            brace_count = 0
            end_pos = start_pos
            
            # Find matching closing brace
            for i in range(start_pos, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            if brace_count == 0:  # Found complete JSON object
                json_candidate = response_text[start_pos:end_pos]
                json_matches.append(json_candidate)
        
        if json_matches:
            # Try to parse each found JSON object, starting with the largest (most complete)
            json_matches.sort(key=len, reverse=True)
            for potential_json_string in json_matches:
                try:
                    # Attempt to clean and parse
                    cleaned_json = _clean_json_string(potential_json_string)
                    # Try to load to check validity
                    json.loads(cleaned_json)
                    json_string = cleaned_json
                    break # Found a valid JSON string, use this one
                except json.JSONDecodeError:
                    continue # Not valid JSON, try next one
        
        if 'json_string' not in locals(): # If no valid JSON found after all attempts
            json_string = response_text # Last resort, use entire response
    
    # Clean the final extracted JSON string
    json_string = _clean_json_string(json_string)
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cleaned JSON: {e}")
        logger.debug(f"Cleaned JSON string: {json_string[:500]}...")
        raise ValueError(f"Invalid JSON after cleaning: {e}")


def _clean_json_string(json_string: str) -> str:
    """
    Clean a JSON string by removing problematic patterns.
    
    Args:
        json_string: Raw JSON string to clean
        
    Returns:
        Cleaned JSON string
    """
    # Remove line-start comments only (avoid removing 'https://' inside strings)
    cleaned = re.sub(r'^\s*//.*$', '', json_string, flags=re.MULTILINE)
    
    # Remove backticks from quoted strings more comprehensively
    # Handle: "url": "`https://example.com`" -> "url": "https://example.com"
    cleaned = re.sub(r'"\s*`([^`]*)`\s*"', r'"\1"', cleaned)
    
    # Handle backticks within quoted strings: "some `text` here" -> "some text here"
    cleaned = re.sub(r'"([^"]*)`([^`]*)`([^"]*?)"', r'"\1\2\3"', cleaned)
    
    # Handle the specific case: " `url` " -> "url"  
    cleaned = re.sub(r'"\s+`([^`]+)`\s+"', r'"\1"', cleaned)
    
    # Trim whitespace inside quoted values after a colon
    cleaned = re.sub(r':\s*"\s+([^"]*?)\s+"\s*', r': "\1"', cleaned)
    
    # IMPORTANT: Do NOT escape structural newlines globally; JSON allows whitespace/newlines between tokens.
    # Only remove invalid control characters that are not valid JSON whitespace.
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)
    
    return cleaned.strip()

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