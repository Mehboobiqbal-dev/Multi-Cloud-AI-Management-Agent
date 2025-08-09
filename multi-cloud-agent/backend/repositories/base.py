from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc
from pydantic import BaseModel

from models.base import BaseModel as DBBaseModel
from core.exceptions import ResourceNotFoundError

# Define type variables for the generic repository
T = TypeVar('T', bound=DBBaseModel)  # Database model type
C = TypeVar('C', bound=BaseModel)    # Create schema type
U = TypeVar('U', bound=BaseModel)    # Update schema type

class BaseRepository(Generic[T, C, U]):
    """
    Base repository class with common CRUD operations.
    """
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize the repository with a database session and model class.
        """
        self.db = db
        self.model = model
    
    def get(self, id: int) -> Optional[T]:
        """
        Get a record by ID.
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_or_404(self, id: int) -> T:
        """
        Get a record by ID or raise a 404 error.
        """
        obj = self.get(id)
        if obj is None:
            raise ResourceNotFoundError(f"{self.model.__name__} with id {id} not found")
        return obj
    
    def get_by(self, **kwargs) -> Optional[T]:
        """
        Get a record by arbitrary filters.
        """
        return self.db.query(self.model).filter_by(**kwargs).first()
    
    def get_by_or_404(self, **kwargs) -> T:
        """
        Get a record by arbitrary filters or raise a 404 error.
        """
        obj = self.get_by(**kwargs)
        if obj is None:
            filters_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            raise ResourceNotFoundError(f"{self.model.__name__} with {filters_str} not found")
        return obj
    
    def list(self, 
             skip: int = 0, 
             limit: int = 100, 
             filters: Dict[str, Any] = None,
             sort_by: str = None,
             sort_order: str = "asc") -> List[T]:
        """
        List records with pagination, filtering, and sorting.
        """
        query = self.db.query(self.model)
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        # Apply sorting if provided
        if sort_by and hasattr(self.model, sort_by):
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(self.model, sort_by)))
            else:
                query = query.order_by(asc(getattr(self.model, sort_by)))
        else:
            # Default sort by id
            query = query.order_by(self.model.id)
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        Count records with optional filtering.
        """
        query = self.db.query(func.count(self.model.id))
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.scalar()
    
    def create(self, obj_in: Union[C, Dict[str, Any]]) -> T:
        """
        Create a new record.
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)
        
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: T, obj_in: Union[U, Dict[str, Any]]) -> T:
        """
        Update an existing record.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Only update fields that are actually present in the update data
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """
        Delete a record by ID.
        """
        obj = self.get_or_404(id)
        self.db.delete(obj)
        self.db.commit()
        return True
    
    def delete_by(self, **kwargs) -> bool:
        """
        Delete records by arbitrary filters.
        """
        objs = self.db.query(self.model).filter_by(**kwargs).all()
        for obj in objs:
            self.db.delete(obj)
        self.db.commit()
        return True