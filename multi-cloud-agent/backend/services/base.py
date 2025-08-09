from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Union
from pydantic import BaseModel
from sqlalchemy.orm import Session

from repositories.base import BaseRepository
from models.base import BaseModel as DBBaseModel
from core.exceptions import ResourceNotFoundError

# Define type variables for the generic service
T = TypeVar('T', bound=DBBaseModel)  # Database model type
R = TypeVar('R', bound=BaseRepository)  # Repository type
C = TypeVar('C', bound=BaseModel)    # Create schema type
U = TypeVar('U', bound=BaseModel)    # Update schema type

class BaseService(Generic[T, R, C, U]):
    """
    Base service class with common business logic operations.
    """
    def __init__(self, repository: R):
        """
        Initialize the service with a repository.
        """
        self.repository = repository
    
    def get(self, id: int) -> Optional[T]:
        """
        Get a record by ID.
        """
        return self.repository.get(id)
    
    def get_or_404(self, id: int) -> T:
        """
        Get a record by ID or raise a 404 error.
        """
        return self.repository.get_or_404(id)
    
    def get_by(self, **kwargs) -> Optional[T]:
        """
        Get a record by arbitrary filters.
        """
        return self.repository.get_by(**kwargs)
    
    def get_by_or_404(self, **kwargs) -> T:
        """
        Get a record by arbitrary filters or raise a 404 error.
        """
        return self.repository.get_by_or_404(**kwargs)
    
    def list(self, 
             skip: int = 0, 
             limit: int = 100, 
             filters: Dict[str, Any] = None,
             sort_by: str = None,
             sort_order: str = "asc") -> List[T]:
        """
        List records with pagination, filtering, and sorting.
        """
        return self.repository.list(skip, limit, filters, sort_by, sort_order)
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records with optional filtering.
        """
        return self.repository.count(filters)
    
    def create(self, obj_in: Union[C, Dict[str, Any]]) -> T:
        """
        Create a new record.
        """
        return self.repository.create(obj_in)
    
    def update(self, id: int, obj_in: Union[U, Dict[str, Any]]) -> T:
        """
        Update an existing record by ID.
        """
        db_obj = self.repository.get_or_404(id)
        return self.repository.update(db_obj, obj_in)
    
    def delete(self, id: int) -> bool:
        """
        Delete a record by ID.
        """
        return self.repository.delete(id)
    
    def delete_by(self, **kwargs) -> bool:
        """
        Delete records by arbitrary filters.
        """
        return self.repository.delete_by(**kwargs)
    
    def get_paginated_response(self, 
                              page: int = 1, 
                              page_size: int = 10, 
                              filters: Dict[str, Any] = None,
                              sort_by: str = None,
                              sort_order: str = "asc") -> Dict[str, Any]:
        """
        Get a paginated response with metadata.
        """
        # Calculate skip based on page and page_size
        skip = (page - 1) * page_size
        
        # Get items for the current page
        items = self.list(skip, page_size, filters, sort_by, sort_order)
        
        # Get total count
        total = self.count(filters)
        
        # Calculate total pages
        pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        # Return paginated response
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }