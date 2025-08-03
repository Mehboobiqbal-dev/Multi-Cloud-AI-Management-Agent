# Core package initialization

# Import key components for easier access
from core.config import settings
from core.logging import setup_logging, get_logger
from core.exceptions import (
    BaseAppException,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
    RateLimitExceededError
)

# Version information
__version__ = "1.0.0"