from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session

from services.base import BaseService
from repositories.cloud_credential import CloudCredentialRepository
from models.cloud_credential import CloudCredential
from schemas.cloud_credential import (
    CloudCredentialCreate, CloudCredentialUpdate,
    AWSCredentialCreate, AzureCredentialCreate, GCPCredentialCreate
)
from core.security import encrypt, decrypt
from core.exceptions import ValidationError, ResourceNotFoundError

class CloudCredentialService(BaseService[CloudCredential, CloudCredentialRepository, CloudCredentialCreate, CloudCredentialUpdate]):
    """
    Service for cloud credential operations.
    """
    def __init__(self, repository: CloudCredentialRepository):
        super().__init__(repository)
    
    def get_by_user_id(self, user_id: int, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Get credentials for a specific user with pagination.
        """
        return self.get_paginated_response(
            page=page,
            page_size=page_size,
            filters={"user_id": user_id}
        )
    
    def get_by_user_and_provider(self, user_id: int, provider: str) -> List[CloudCredential]:
        """
        Get credentials for a specific user and provider.
        """
        return self.repository.get_by_user_and_provider(user_id, provider)
    
    def get_by_user_and_name(self, user_id: int, name: str) -> Optional[CloudCredential]:
        """
        Get a credential by user ID and name.
        """
        return self.repository.get_by_user_and_name(user_id, name)
    
    def get_by_user_and_name_or_404(self, user_id: int, name: str) -> CloudCredential:
        """
        Get a credential by user ID and name or raise a 404 error.
        """
        credential = self.get_by_user_and_name(user_id, name)
        if credential is None:
            raise ResourceNotFoundError(f"Credential with name {name} not found for user {user_id}")
        return credential
    
    def create_aws_credential(self, user_id: int, credential_in: AWSCredentialCreate) -> CloudCredential:
        """
        Create a new AWS credential.
        """
        # Check if credential with this name already exists for the user
        existing_credential = self.get_by_user_and_name(user_id, credential_in.name)
        if existing_credential:
            raise ValidationError(f"Credential with name {credential_in.name} already exists for this user")
        
        # Encrypt sensitive data
        encrypted_access_key_id = encrypt(credential_in.access_key_id)
        encrypted_secret_access_key = encrypt(credential_in.secret_access_key)
        
        # Create credential
        return self.repository.create_aws_credential(
            user_id=user_id,
            name=credential_in.name,
            encrypted_access_key_id=encrypted_access_key_id,
            encrypted_secret_access_key=encrypted_secret_access_key,
            region=credential_in.region
        )
    
    def create_azure_credential(self, user_id: int, credential_in: AzureCredentialCreate) -> CloudCredential:
        """
        Create a new Azure credential.
        """
        # Check if credential with this name already exists for the user
        existing_credential = self.get_by_user_and_name(user_id, credential_in.name)
        if existing_credential:
            raise ValidationError(f"Credential with name {credential_in.name} already exists for this user")
        
        # Encrypt sensitive data
        encrypted_tenant_id = encrypt(credential_in.tenant_id)
        encrypted_client_id = encrypt(credential_in.client_id)
        encrypted_client_secret = encrypt(credential_in.client_secret)
        encrypted_subscription_id = encrypt(credential_in.subscription_id)
        
        # Create credential
        return self.repository.create_azure_credential(
            user_id=user_id,
            name=credential_in.name,
            encrypted_tenant_id=encrypted_tenant_id,
            encrypted_client_id=encrypted_client_id,
            encrypted_client_secret=encrypted_client_secret,
            encrypted_subscription_id=encrypted_subscription_id
        )
    
    def create_gcp_credential(self, user_id: int, credential_in: GCPCredentialCreate) -> CloudCredential:
        """
        Create a new GCP credential.
        """
        # Check if credential with this name already exists for the user
        existing_credential = self.get_by_user_and_name(user_id, credential_in.name)
        if existing_credential:
            raise ValidationError(f"Credential with name {credential_in.name} already exists for this user")
        
        # Encrypt sensitive data
        encrypted_service_account_key = encrypt(credential_in.service_account_key)
        
        # Create credential
        return self.repository.create_gcp_credential(
            user_id=user_id,
            name=credential_in.name,
            encrypted_service_account_key=encrypted_service_account_key,
            project_id=credential_in.project_id
        )
    
    def create_credential(self, user_id: int, credential_in: Union[AWSCredentialCreate, AzureCredentialCreate, GCPCredentialCreate]) -> CloudCredential:
        """
        Create a new cloud credential based on provider type.
        """
        if isinstance(credential_in, AWSCredentialCreate):
            return self.create_aws_credential(user_id, credential_in)
        elif isinstance(credential_in, AzureCredentialCreate):
            return self.create_azure_credential(user_id, credential_in)
        elif isinstance(credential_in, GCPCredentialCreate):
            return self.create_gcp_credential(user_id, credential_in)
        else:
            raise ValidationError(f"Unsupported credential type: {type(credential_in)}")
    
    def get_decrypted_aws_credentials(self, credential_id: int) -> Dict[str, Any]:
        """
        Get decrypted AWS credentials.
        """
        credential = self.get_or_404(credential_id)
        
        if credential.provider != "aws":
            raise ValidationError(f"Credential {credential_id} is not an AWS credential")
        
        return {
            "access_key_id": decrypt(credential.aws_access_key_id) if credential.aws_access_key_id else None,
            "secret_access_key": decrypt(credential.aws_secret_access_key) if credential.aws_secret_access_key else None,
            "region": credential.aws_region
        }
    
    def get_decrypted_azure_credentials(self, credential_id: int) -> Dict[str, Any]:
        """
        Get decrypted Azure credentials.
        """
        credential = self.get_or_404(credential_id)
        
        if credential.provider != "azure":
            raise ValidationError(f"Credential {credential_id} is not an Azure credential")
        
        return {
            "tenant_id": decrypt(credential.azure_tenant_id) if credential.azure_tenant_id else None,
            "client_id": decrypt(credential.azure_client_id) if credential.azure_client_id else None,
            "client_secret": decrypt(credential.azure_client_secret) if credential.azure_client_secret else None,
            "subscription_id": decrypt(credential.azure_subscription_id) if credential.azure_subscription_id else None
        }
    
    def get_decrypted_gcp_credentials(self, credential_id: int) -> Dict[str, Any]:
        """
        Get decrypted GCP credentials.
        """
        credential = self.get_or_404(credential_id)
        
        if credential.provider != "gcp":
            raise ValidationError(f"Credential {credential_id} is not a GCP credential")
        
        return {
            "service_account_key": decrypt(credential.gcp_service_account_key) if credential.gcp_service_account_key else None,
            "project_id": credential.gcp_project_id
        }
    
    def delete_by_user_id(self, user_id: int) -> bool:
        """
        Delete all credentials for a specific user.
        """
        return self.repository.delete_by_user_id(user_id)