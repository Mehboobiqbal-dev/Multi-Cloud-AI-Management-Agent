from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

from schemas.base import BaseSchema, BaseResponseSchema
from schemas.user import User

class LoginRequest(BaseSchema):
    """
    Schema for login request.
    """
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }

class GoogleLoginRequest(BaseSchema):
    """
    Schema for Google login request.
    """
    id_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFiZDY4NWY1ZThmMzc..."
            }
        }

class LoginResponse(BaseResponseSchema):
    """
    Schema for login response.
    """
    access_token: str
    token_type: str = "bearer"
    expires_at: int  # Unix timestamp
    user: User
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Login successful",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_at": 1672531200,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "name": "John Doe",
                    "is_active": True,
                    "is_superuser": False
                }
            }
        }

class PasswordResetRequest(BaseSchema):
    """
    Schema for password reset request.
    """
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class PasswordResetConfirm(BaseSchema):
    """
    Schema for password reset confirmation.
    """
    token: str
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    
    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "password": "newsecurepassword123",
                "password_confirm": "newsecurepassword123"
            }
        }

class ChangePasswordRequest(BaseSchema):
    """
    Schema for changing password.
    """
    current_password: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str = Field(..., min_length=8)
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "securepassword123",
                "new_password": "newsecurepassword123",
                "new_password_confirm": "newsecurepassword123"
            }
        }