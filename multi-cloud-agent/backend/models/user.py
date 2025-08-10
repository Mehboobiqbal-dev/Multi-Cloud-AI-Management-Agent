from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from typing import List, Optional

from models.base import BaseModel

class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    __tablename__ = 'users'
    
    # Basic user information
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    
    # OAuth information
    google_id = Column(String, unique=True, index=True, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    credentials = relationship("CloudCredential", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    plan_histories = relationship("PlanHistory", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    agent_sessions = relationship("AgentSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"