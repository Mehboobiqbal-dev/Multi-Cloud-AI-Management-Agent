from typing import Any, Dict, Optional, List
from fastapi import HTTPException, status

class BaseAppException(Exception):
    """
    Base exception class for application-specific exceptions.
    """
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to a dictionary for API responses.
        """
        return {
            "status": "error",
            "message": self.message,
            "status_code": self.status_code,
            "detail": self.detail
        }

    def to_http_exception(self) -> HTTPException:
        """
        Convert to FastAPI HTTPException.
        """
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )

class AuthenticationError(BaseAppException):
    """
    Exception raised for authentication errors.
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        detail: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class AuthorizationError(BaseAppException):
    """
    Exception raised for authorization errors.
    """
    def __init__(
        self,
        message: str = "Not authorized to perform this action",
        detail: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ResourceNotFoundError(BaseAppException):
    """
    Exception raised when a requested resource is not found.
    """
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[Any] = None,
        message: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            if resource_id is not None:
                message = f"{resource_type} with id {resource_id} not found"
            else:
                message = f"{resource_type} not found"
                
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or {"resource_type": resource_type, "resource_id": resource_id}
        )

class ValidationError(BaseAppException):
    """
    Exception raised for validation errors.
    """
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[List[Dict[str, Any]]] = None,
        detail: Optional[Dict[str, Any]] = None
    ):
        if detail is None:
            detail = {}
            
        if errors:
            detail["errors"] = errors
            
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

class ExternalServiceError(BaseAppException):
    """
    Exception raised when an external service call fails.
    """
    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
        original_error: Optional[Exception] = None,
        detail: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Error calling external service: {service_name}"
            
        if detail is None:
            detail = {}
            
        detail["service_name"] = service_name
        
        if original_error:
            detail["original_error"] = str(original_error)
            
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail
        )

class RateLimitExceededError(BaseAppException):
    """
    Exception raised when rate limit is exceeded.
    """
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        detail: Optional[Dict[str, Any]] = None
    ):
        if detail is None:
            detail = {}
            
        if retry_after:
            detail["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )