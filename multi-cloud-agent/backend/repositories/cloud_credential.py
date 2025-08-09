from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from repositories.base import BaseRepository
from models.cloud_credential import CloudCredential
from schemas.cloud_credential import CloudCredentialCreate, CloudCredentialUpdate

class CloudCredentialRepository(BaseRepository[CloudCredential, CloudCredentialCreate, CloudCredentialUpdate]):
    """
    Repository for CloudCredential model operations.
    """
    def __init__(self, db: Session):
        super().__init__(db, CloudCredential)
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[CloudCredential]:
        """
        Get credentials for a specific user with pagination.
        """
        return self.db.query(CloudCredential).filter(CloudCredential.user_id == user_id).offset(skip).limit(limit).all()
    
    def count_by_user_id(self, user_id: int) -> int:
        """
        Count credentials for a specific user.
        """
        return self.db.query(CloudCredential).filter(CloudCredential.user_id == user_id).count()
    
    def get_by_user_and_provider(self, user_id: int, provider: str) -> List[CloudCredential]:
        """
        Get credentials for a specific user and provider.
        """
        return self.db.query(CloudCredential).filter(
            CloudCredential.user_id == user_id,
            CloudCredential.provider == provider
        ).all()
    
    def get_by_user_and_name(self, user_id: int, name: str) -> Optional[CloudCredential]:
        """
        Get a credential by user ID and name.
        """
        return self.db.query(CloudCredential).filter(
            CloudCredential.user_id == user_id,
            CloudCredential.name == name
        ).first()
    
    def create_aws_credential(
        self, user_id: int, name: str, encrypted_access_key_id: str, 
        encrypted_secret_access_key: str, region: Optional[str] = None
    ) -> CloudCredential:
        """
        Create a new AWS credential.
        """
        db_obj = CloudCredential(
            user_id=user_id,
            provider="aws",
            name=name,
            aws_access_key_id=encrypted_access_key_id,
            aws_secret_access_key=encrypted_secret_access_key,
            aws_region=region
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def create_azure_credential(
        self, user_id: int, name: str, encrypted_tenant_id: str, 
        encrypted_client_id: str, encrypted_client_secret: str, 
        encrypted_subscription_id: str
    ) -> CloudCredential:
        """
        Create a new Azure credential.
        """
        db_obj = CloudCredential(
            user_id=user_id,
            provider="azure",
            name=name,
            azure_tenant_id=encrypted_tenant_id,
            azure_client_id=encrypted_client_id,
            azure_client_secret=encrypted_client_secret,
            azure_subscription_id=encrypted_subscription_id
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def create_gcp_credential(
        self, user_id: int, name: str, encrypted_service_account_key: str, 
        project_id: Optional[str] = None
    ) -> CloudCredential:
        """
        Create a new GCP credential.
        """
        db_obj = CloudCredential(
            user_id=user_id,
            provider="gcp",
            name=name,
            gcp_service_account_key=encrypted_service_account_key,
            gcp_project_id=project_id
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete_by_user_id(self, user_id: int) -> bool:
        """
        Delete all credentials for a specific user.
        """
        objs = self.db.query(CloudCredential).filter(CloudCredential.user_id == user_id).all()
        for obj in objs:
            self.db.delete(obj)
        self.db.commit()
        return True