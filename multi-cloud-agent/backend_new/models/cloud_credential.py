from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from models.base import BaseModel

class CloudCredential(BaseModel):
    """
    Model for storing cloud provider credentials.
    All sensitive fields are stored encrypted.
    """
    # Relationship to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="credentials")
    
    # Cloud provider information
    provider = Column(String, nullable=False)  # aws, azure, gcp
    name = Column(String, nullable=False)  # User-friendly name for the credential
    
    # AWS credentials
    access_key = Column(String, nullable=True)  # Encrypted
    secret_key = Column(String, nullable=True)  # Encrypted
    
    # Azure credentials
    azure_subscription_id = Column(String, nullable=True)  # Encrypted
    azure_client_id = Column(String, nullable=True)  # Encrypted
    azure_client_secret = Column(String, nullable=True)  # Encrypted
    azure_tenant_id = Column(String, nullable=True)  # Encrypted
    
    # GCP credentials
    gcp_project_id = Column(String, nullable=True)  # Encrypted
    gcp_credentials_json = Column(String, nullable=True)  # Encrypted JSON string
    
    def __repr__(self) -> str:
        return f"<CloudCredential(id={self.id}, provider='{self.provider}', name='{self.name}')>"