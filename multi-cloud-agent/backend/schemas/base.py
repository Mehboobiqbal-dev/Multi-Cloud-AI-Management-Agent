from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime

# Define a type variable for generic models
T = TypeVar('T')

class BaseSchema(BaseModel):
    """
    Base schema with common configuration.
    """
    class Config:
        # Allow conversion from ORM models
        from_attributes = True
        # Validate assignment to model fields
        validate_assignment = True
        # Use JSON schema extra fields
        json_schema_extra = {"example": {}}

class BaseResponseSchema(BaseSchema):
    """
    Base schema for API responses.
    """
    status: str = "success"
    message: Optional[str] = None

class PaginatedResponseSchema(BaseResponseSchema, Generic[T]):
    """
    Schema for paginated responses.
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

class ErrorResponseSchema(BaseSchema):
    """
    Schema for error responses.
    """
    status: str = "error"
    message: str
    error_type: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None

class TokenSchema(BaseSchema):
    """
    Schema for authentication tokens.
    """
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class PaginationQuerySchema(BaseSchema):
    """
    Schema for pagination query parameters.
    """
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page")
    
    @validator('page_size')
    def validate_page_size(cls, v):
        """
        Validate page_size is within reasonable limits.
        """
        if v > 100:
            return 100
        return v

class SortQuerySchema(BaseSchema):
    """
    Schema for sorting query parameters.
    """
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """
        Validate sort_order is either asc or desc.
        """
        if v not in ["asc", "desc"]:
            return "asc"
        return v