import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

from core.config import settings

# Define log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def setup_logging(log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_file: Optional path to log file. If not provided, logs will only go to stdout.
    """
    # Get log level from settings
    log_level = LOG_LEVELS.get(settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:  
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        
        # Create rotating file handler (10 MB max size, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup message
    logging.info(f"Logging initialized at {settings.LOG_LEVEL} level")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger, typically __name__ of the module.
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def log_request(request_data: Dict[str, Any], user_id: Optional[int] = None) -> None:
    """
    Log an API request with relevant details.
    
    Args:
        request_data: Dictionary containing request details.
        user_id: Optional user ID associated with the request.
    """
    logger = get_logger("api.request")
    
    # Create a sanitized copy of request data (remove sensitive fields)
    safe_data = request_data.copy()
    for sensitive_field in ["password", "token", "access_key", "secret_key", "api_key"]:
        if sensitive_field in safe_data:
            safe_data[sensitive_field] = "[REDACTED]"
    
    # Log the request
    logger.info(
        f"Request: {safe_data.get('method', 'UNKNOWN')} {safe_data.get('path', 'UNKNOWN')} "
        f"| User: {user_id or 'anonymous'} | IP: {safe_data.get('client', 'unknown')}"
    )

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with context information.
    
    Args:
        error: The exception that occurred.
        context: Optional dictionary with additional context information.
    """
    logger = get_logger("api.error")
    
    # Create context string if provided
    context_str = f" | Context: {context}" if context else ""
    
    # Log the error with context
    logger.error(f"Error: {str(error)}{context_str}", exc_info=True)