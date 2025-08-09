from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from schemas.base import BaseSchema, BaseResponseSchema

class AuditLogBase(BaseSchema):
    """
    Base schema for audit log data.
    """
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "success"
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "login",
                "resource_type": "user",
                "resource_id": "1",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "details": {"method": "password"},
                "status": "success"
            }
        }

class AuditLogCreate(AuditLogBase):
    """
    Schema for creating a new audit log.
    """
    user_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "action": "login",
                "resource_type": "user",
                "resource_id": "1",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "details": {"method": "password"},
                "status": "success"
            }
        }

class AuditLog(AuditLogBase):
    """
    Schema for audit log data returned to clients.
    """
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "action": "login",
                "resource_type": "user",
                "resource_id": "1",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "details": {"method": "password"},
                "status": "success",
                "created_at": "2023-01-01T00:00:00"
            }
        }

class AuditLogResponse(BaseResponseSchema):
    """
    Schema for audit log response.
    """
    data: AuditLog
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Audit log retrieved successfully",
                "data": {
                    "id": 1,
                    "user_id": 1,
                    "action": "login",
                    "resource_type": "user",
                    "resource_id": "1",
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "details": {"method": "password"},
                    "status": "success",
                    "created_at": "2023-01-01T00:00:00"
                }
            }
        }

class AuditLogsResponse(BaseResponseSchema):
    """
    Schema for multiple audit logs response.
    """
    data: List[AuditLog]
    total: int
    page: int
    page_size: int
    pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Audit logs retrieved successfully",
                "data": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "action": "login",
                        "resource_type": "user",
                        "resource_id": "1",
                        "ip_address": "192.168.1.1",
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "details": {"method": "password"},
                        "status": "success",
                        "created_at": "2023-01-01T00:00:00"
                    },
                    {
                        "id": 2,
                        "user_id": 1,
                        "action": "create_resource",
                        "resource_type": "vm",
                        "resource_id": "vm-123",
                        "ip_address": "192.168.1.1",
                        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "details": {"provider": "aws", "instance_type": "t2.micro"},
                        "status": "success",
                        "created_at": "2023-01-01T00:00:00"
                    }
                ],
                "total": 2,
                "page": 1,
                "page_size": 10,
                "pages": 1
            }
        }