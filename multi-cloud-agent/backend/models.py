from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    google_id = Column(String, unique=True)
    credentials = relationship('CloudCredential', back_populates='user')

class CloudCredential(Base):
    __tablename__ = 'cloud_credentials'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(String)  # aws, azure, gcp
    access_key = Column(String)  # For AWS
    secret_key = Column(String)  # For AWS
    azure_subscription_id = Column(String)  # For Azure
    azure_client_id = Column(String)
    azure_client_secret = Column(String)
    azure_tenant_id = Column(String)
    gcp_project_id = Column(String)
    gcp_credentials_json = Column(String)  # Store as encrypted JSON string
    user = relationship('User', back_populates='credentials')