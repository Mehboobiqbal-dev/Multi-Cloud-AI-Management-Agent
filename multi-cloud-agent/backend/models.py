from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    google_id = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    credentials = relationship('CloudCredential', back_populates='user')
    audit_logs = relationship('AuditLog', back_populates='user')
    plan_histories = relationship('PlanHistory', back_populates='user')
    chat_messages = relationship('ChatHistory', back_populates='user')
    agent_sessions = relationship('AgentSession', back_populates='user')

class CloudCredential(Base):
    __tablename__ = 'cloud_credentials'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    provider = Column(String, nullable=False)  # aws, azure, gcp
    access_key = Column(String)  # Encrypted
    secret_key = Column(String)  # Encrypted
    azure_subscription_id = Column(String)  # For Azure
    azure_client_id = Column(String)
    azure_client_secret = Column(String)
    azure_tenant_id = Column(String)
    gcp_project_id = Column(String)
    gcp_credentials_json = Column(String)  # Store as encrypted JSON string
    user = relationship('User', back_populates='credentials')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='audit_logs')

class PlanHistory(Base):
    __tablename__ = 'plan_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    prompt = Column(Text, nullable=False)
    plan = Column(Text) # JSON of the plan
    status = Column(String) # 'requires_feedback', 'success', 'failure'
    execution_results = Column(Text) # JSON of the execution steps
    feedback = Column(String, nullable=True) # 'success', 'failure'
    correction = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='plan_histories')

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'agent'
    message = Column(Text, nullable=False)
    message_type = Column(String, default='text')  # 'text', 'command', 'assistance'
    agent_run_id = Column(String, nullable=True)  # Link to specific agent run
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='chat_messages')

class AgentSession(Base):
    __tablename__ = 'agent_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    run_id = Column(String, unique=True, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, default='running')  # 'running', 'paused', 'completed', 'failed'
    current_step = Column(Integer, default=0)
    history = Column(Text)  # JSON of execution history
    awaiting_assistance = Column(Boolean, default=False)
    assistance_request = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship('User', back_populates='agent_sessions')
