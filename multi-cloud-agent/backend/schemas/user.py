from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

from schemas.base import BaseSchema, BaseResponseSchema

class UserBase(BaseSchema):
    """
    Base schema for user data.
    """
    email: EmailStr
    name: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe"
            }
        }

class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """
    password: Optional[str] = Field(None, min_length=8)
    google_id: Optional[str] = None
    
    @validator('password')
    def password_or_google_id_required(cls, v, values):
        """
        Validate that either password or google_id is provided.
        """
        if not v and not values.get('google_id'):
            raise ValueError('Either password or google_id must be provided')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "password": "securepassword123"
            }
        }

class UserUpdate(BaseSchema):
    """
    Schema for updating an existing user.
    """
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Smith",
                "password": "newsecurepassword123"
            }
        }

class UserInDB(UserBase):
    """
    Schema for user data from the database.
    """
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class User(UserBase):
    """
    Schema for user data returned to clients.
    """
    id: int
    is_active: bool
    is_superuser: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "name": "John Doe",
                "is_active": True,
                "is_superuser": False
            }
        }

class UserResponse(BaseResponseSchema):
    """
    Schema for user response.
    """
    data: User
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "User retrieved successfully",
                "data": {
                    "id": 1,
                    "email": "user@example.com",
                    "name": "John Doe",
                    "is_active": True,
                    "is_superuser": False
                }
            }
        }

class UsersResponse(BaseResponseSchema):
    """
    Schema for multiple users response.
    """
    data: List[User]
    total: int
    page: int
    page_size: int
    pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Users retrieved successfully",
                "data": [
                    {
                        "id": 1,
                        "email": "user1@example.com",
                        "name": "John Doe",
                        "is_active": True,
                        "is_superuser": False
                    },
                    {
                        "id": 2,
                        "email": "user2@example.com",
                        "name": "Jane Smith",
                        "is_active": True,
                        "is_superuser": False
                    }
                ],
                "total": 2,
                "page": 1,
                "page_size": 10,
                "pages": 1
            }
        }