from pydantic import BaseModel, Field, validator, RootModel
from typing import Optional, List, Literal
from datetime import datetime

from schemas.base import BaseSchema, BaseResponseSchema

class CloudCredentialBase(BaseSchema):
    """
    Base schema for cloud credentials.
    """
    provider: Literal["aws", "azure", "gcp"]
    name: str = Field(..., min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "aws",
                "name": "My AWS Account"
            }
        }

class AWSCredentialCreate(CloudCredentialBase):
    """
    Schema for creating AWS credentials.
    """
    provider: Literal["aws"] = "aws"
    access_key_id: str
    secret_access_key: str
    region: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "aws",
                "name": "My AWS Account",
                "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "region": "us-west-2"
            }
        }

class AzureCredentialCreate(CloudCredentialBase):
    """
    Schema for creating Azure credentials.
    """
    provider: Literal["azure"] = "azure"
    tenant_id: str
    client_id: str
    client_secret: str
    subscription_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "azure",
                "name": "My Azure Account",
                "tenant_id": "00000000-0000-0000-0000-000000000000",
                "client_id": "00000000-0000-0000-0000-000000000000",
                "client_secret": "client_secret_value",
                "subscription_id": "00000000-0000-0000-0000-000000000000"
            }
        }

class GCPCredentialCreate(CloudCredentialBase):
    """
    Schema for creating GCP credentials.
    """
    provider: Literal["gcp"] = "gcp"
    service_account_key: str  # JSON string of service account key
    project_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "gcp",
                "name": "My GCP Account",
                "service_account_key": "{\"type\": \"service_account\", ...}",
                "project_id": "my-gcp-project"
            }
        }

class CloudCredentialCreate(RootModel):
    """
    Schema for creating cloud credentials (union type).
    """
    root: CloudCredentialBase
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "aws",
                "name": "My AWS Account"
            }
        }

class CloudCredentialUpdate(BaseSchema):
    """
    Schema for updating cloud credentials.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    # Provider-specific fields are handled in the service layer
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated AWS Account Name"
            }
        }

class CloudCredential(CloudCredentialBase):
    """
    Schema for cloud credential data returned to clients.
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    # Sensitive data is not included
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "provider": "aws",
                "name": "My AWS Account",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

class CloudCredentialResponse(BaseResponseSchema):
    """
    Schema for cloud credential response.
    """
    data: CloudCredential
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Cloud credential retrieved successfully",
                "data": {
                    "id": 1,
                    "user_id": 1,
                    "provider": "aws",
                    "name": "My AWS Account",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            }
        }

class CloudCredentialsResponse(BaseResponseSchema):
    """
    Schema for multiple cloud credentials response.
    """
    data: List[CloudCredential]
    total: int
    page: int
    page_size: int
    pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Cloud credentials retrieved successfully",
                "data": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "provider": "aws",
                        "name": "My AWS Account",
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00"
                    },
                    {
                        "id": 2,
                        "user_id": 1,
                        "provider": "azure",
                        "name": "My Azure Account",
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:00:00"
                    }
                ],
                "total": 2,
                "page": 1,
                "page_size": 10,
                "pages": 1
            }
        }