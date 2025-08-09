from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from repositories.base import BaseRepository
from models.user import User
from schemas.user import UserCreate, UserUpdate

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model operations.
    """
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """
        Get a user by Google ID.
        """
        return self.db.query(User).filter(User.google_id == google_id).first()
    
    def create_with_password(self, obj_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user with a hashed password.
        """
        db_obj = User(
            email=obj_in.email,
            name=obj_in.name,
            hashed_password=hashed_password,
            google_id=obj_in.google_id,
            is_active=True,
            is_superuser=False
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update_password(self, user: User, hashed_password: str) -> User:
        """
        Update a user's password.
        """
        user.hashed_password = hashed_password
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get active users with pagination.
        """
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def count_active_users(self) -> int:
        """
        Count active users.
        """
        return self.db.query(User).filter(User.is_active == True).count()
    
    def deactivate(self, user: User) -> User:
        """
        Deactivate a user.
        """
        user.is_active = False
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def activate(self, user: User) -> User:
        """
        Activate a user.
        """
        user.is_active = True
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def make_superuser(self, user: User) -> User:
        """
        Make a user a superuser.
        """
        user.is_superuser = True
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def remove_superuser(self, user: User) -> User:
        """
        Remove superuser status from a user.
        """
        user.is_superuser = False
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user