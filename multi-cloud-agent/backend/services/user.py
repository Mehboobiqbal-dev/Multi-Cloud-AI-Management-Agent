from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from services.base import BaseService
from repositories.user import UserRepository
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password
from core.exceptions import AuthenticationError, ResourceNotFoundError, ValidationError

class UserService(BaseService[User, UserRepository, UserCreate, UserUpdate]):
    """
    Service for user-related operations.
    """
    def __init__(self, repository: UserRepository):
        super().__init__(repository)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        """
        return self.repository.get_by_email(email)
    
    def get_by_email_or_404(self, email: str) -> User:
        """
        Get a user by email or raise a 404 error.
        """
        user = self.get_by_email(email)
        if user is None:
            raise ResourceNotFoundError(f"User with email {email} not found")
        return user
    
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Get a user by Google ID.
        """
        return self.repository.get_by_google_id(google_id)
    
    def create_user(self, user_in: UserCreate) -> User:
        """
        Create a new user.
        """
        # Check if user with this email already exists
        existing_user = self.get_by_email(user_in.email)
        if existing_user:
            raise ValidationError(f"User with email {user_in.email} already exists")
        
        # If password is provided, hash it
        if user_in.password:
            hashed_password = get_password_hash(user_in.password)
            return self.repository.create_with_password(user_in, hashed_password)
        elif user_in.google_id:
            # For Google sign-in, no password is required
            return self.repository.create_with_password(user_in, None)
        else:
            raise ValidationError("Either password or google_id must be provided")
    
    def authenticate(self, email: str, password: str) -> User:
        """
        Authenticate a user with email and password.
        """
        user = self.get_by_email(email)
        if not user:
            raise AuthenticationError("Incorrect email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        if not user.hashed_password:
            raise AuthenticationError("User account does not have a password set")
        
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        
        return user
    
    def authenticate_google(self, google_id: str, email: str, name: Optional[str] = None) -> User:
        """
        Authenticate a user with Google ID, creating if not exists.
        """
        user = self.get_by_google_id(google_id)
        
        # If user doesn't exist, create a new one
        if not user:
            # Check if user with this email already exists
            email_user = self.get_by_email(email)
            if email_user:
                # Link Google ID to existing account
                email_user.google_id = google_id
                return self.repository.update(email_user, {"google_id": google_id})
            else:
                # Create new user with Google ID
                user_in = UserCreate(email=email, name=name, google_id=google_id)
                return self.create_user(user_in)
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        return user
    
    def update_password(self, user_id: int, current_password: str, new_password: str) -> User:
        """
        Update a user's password.
        """
        user = self.get_or_404(user_id)
        
        # Verify current password
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Hash new password
        hashed_password = get_password_hash(new_password)
        
        # Update password
        return self.repository.update_password(user, hashed_password)
    
    def reset_password(self, user_id: int, new_password: str) -> User:
        """
        Reset a user's password (admin or password reset flow).
        """
        user = self.get_or_404(user_id)
        
        # Hash new password
        hashed_password = get_password_hash(new_password)
        
        # Update password
        return self.repository.update_password(user, hashed_password)
    
    def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate a user account.
        """
        user = self.get_or_404(user_id)
        return self.repository.deactivate(user)
    
    def activate_user(self, user_id: int) -> User:
        """
        Activate a user account.
        """
        user = self.get_or_404(user_id)
        return self.repository.activate(user)
    
    def make_superuser(self, user_id: int) -> User:
        """
        Make a user a superuser.
        """
        user = self.get_or_404(user_id)
        return self.repository.make_superuser(user)
    
    def remove_superuser(self, user_id: int) -> User:
        """
        Remove superuser status from a user.
        """
        user = self.get_or_404(user_id)
        return self.repository.remove_superuser(user)
    
    def get_active_users_paginated(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Get active users with pagination.
        """
        return self.get_paginated_response(
            page=page,
            page_size=page_size,
            filters={"is_active": True}
        )