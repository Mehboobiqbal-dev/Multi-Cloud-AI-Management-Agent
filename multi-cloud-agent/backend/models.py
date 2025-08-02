from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    hashed_password = Column(String)
    google_id = Column(String, unique=True, index=True)
    credentials = relationship('CloudCredential', back_populates='user')
    audit_logs = relationship('AuditLog', back_populates='user')

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
    user_id = Column(Integer, ForeignKey('users.id'))
    plan = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User')
