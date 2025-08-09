from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from schemas.base import BaseSchema, BaseResponseSchema

class PlanHistoryBase(BaseSchema):
    """
    Base schema for plan history data.
    """
    prompt: str
    plan: Dict[str, Any]  # JSON structure of the execution plan
    status: Literal["pending", "running", "completed", "failed", "requires_feedback"] = "pending"
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a VM in AWS and install nginx",
                "plan": {
                    "steps": [
                        {"type": "create_vm", "provider": "aws", "params": {"instance_type": "t2.micro"}},
                        {"type": "install_software", "software": "nginx"}
                    ]
                },
                "status": "pending"
            }
        }

class StepExecution(BaseSchema):
    """
    Schema for step execution data.
    """
    step_id: int
    step_type: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PlanHistoryCreate(PlanHistoryBase):
    """
    Schema for creating a new plan history.
    """
    user_id: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "prompt": "Create a VM in AWS and install nginx",
                "plan": {
                    "steps": [
                        {"type": "create_vm", "provider": "aws", "params": {"instance_type": "t2.micro"}},
                        {"type": "install_software", "software": "nginx"}
                    ]
                },
                "status": "pending"
            }
        }

class PlanHistoryUpdate(BaseSchema):
    """
    Schema for updating an existing plan history.
    """
    status: Optional[Literal["pending", "running", "completed", "failed", "requires_feedback"]] = None
    execution_results: Optional[List[StepExecution]] = None
    final_result: Optional[Dict[str, Any]] = None
    feedback: Optional[Literal["positive", "negative"]] = None
    correction: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "execution_results": [
                    {
                        "step_id": 1,
                        "step_type": "create_vm",
                        "status": "completed",
                        "start_time": "2023-01-01T00:00:00",
                        "end_time": "2023-01-01T00:05:00",
                        "result": {"instance_id": "i-1234567890abcdef0"}
                    },
                    {
                        "step_id": 2,
                        "step_type": "install_software",
                        "status": "completed",
                        "start_time": "2023-01-01T00:05:00",
                        "end_time": "2023-01-01T00:07:00",
                        "result": {"status": "installed"}
                    }
                ],
                "final_result": {"message": "VM created and nginx installed successfully"}
            }
        }

class FeedbackCreate(BaseSchema):
    """
    Schema for creating feedback for a plan.
    """
    feedback: Literal["positive", "negative"]
    correction: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "negative",
                "correction": "I wanted to install Apache, not Nginx"
            }
        }

class PlanHistory(PlanHistoryBase):
    """
    Schema for plan history data returned to clients.
    """
    id: int
    user_id: int
    execution_results: Optional[List[StepExecution]] = None
    final_result: Optional[Dict[str, Any]] = None
    feedback: Optional[Literal["positive", "negative"]] = None
    correction: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "prompt": "Create a VM in AWS and install nginx",
                "plan": {
                    "steps": [
                        {"type": "create_vm", "provider": "aws", "params": {"instance_type": "t2.micro"}},
                        {"type": "install_software", "software": "nginx"}
                    ]
                },
                "status": "completed",
                "execution_results": [
                    {
                        "step_id": 1,
                        "step_type": "create_vm",
                        "status": "completed",
                        "start_time": "2023-01-01T00:00:00",
                        "end_time": "2023-01-01T00:05:00",
                        "result": {"instance_id": "i-1234567890abcdef0"}
                    },
                    {
                        "step_id": 2,
                        "step_type": "install_software",
                        "status": "completed",
                        "start_time": "2023-01-01T00:05:00",
                        "end_time": "2023-01-01T00:07:00",
                        "result": {"status": "installed"}
                    }
                ],
                "final_result": {"message": "VM created and nginx installed successfully"},
                "feedback": "positive",
                "correction": None,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:07:00"
            }
        }

class PlanHistoryResponse(BaseResponseSchema):
    """
    Schema for plan history response.
    """
    data: PlanHistory
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Plan history retrieved successfully",
                "data": {
                    "id": 1,
                    "user_id": 1,
                    "prompt": "Create a VM in AWS and install nginx",
                    "plan": {
                        "steps": [
                            {"type": "create_vm", "provider": "aws", "params": {"instance_type": "t2.micro"}},
                            {"type": "install_software", "software": "nginx"}
                        ]
                    },
                    "status": "completed",
                    "execution_results": [
                        {
                            "step_id": 1,
                            "step_type": "create_vm",
                            "status": "completed",
                            "start_time": "2023-01-01T00:00:00",
                            "end_time": "2023-01-01T00:05:00",
                            "result": {"instance_id": "i-1234567890abcdef0"}
                        },
                        {
                            "step_id": 2,
                            "step_type": "install_software",
                            "status": "completed",
                            "start_time": "2023-01-01T00:05:00",
                            "end_time": "2023-01-01T00:07:00",
                            "result": {"status": "installed"}
                        }
                    ],
                    "final_result": {"message": "VM created and nginx installed successfully"},
                    "feedback": "positive",
                    "correction": None,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:07:00"
                }
            }
        }

class PlanHistoriesResponse(BaseResponseSchema):
    """
    Schema for multiple plan histories response.
    """
    data: List[PlanHistory]
    total: int
    page: int
    page_size: int
    pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Plan histories retrieved successfully",
                "data": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "prompt": "Create a VM in AWS and install nginx",
                        "plan": {
                            "steps": [
                                {"type": "create_vm", "provider": "aws", "params": {"instance_type": "t2.micro"}},
                                {"type": "install_software", "software": "nginx"}
                            ]
                        },
                        "status": "completed",
                        "final_result": {"message": "VM created and nginx installed successfully"},
                        "created_at": "2023-01-01T00:00:00",
                        "updated_at": "2023-01-01T00:07:00"
                    },
                    {
                        "id": 2,
                        "user_id": 1,
                        "prompt": "Create an S3 bucket",
                        "plan": {
                            "steps": [
                                {"type": "create_bucket", "provider": "aws", "params": {"name": "my-bucket"}}
                            ]
                        },
                        "status": "completed",
                        "final_result": {"message": "S3 bucket created successfully"},
                        "created_at": "2023-01-02T00:00:00",
                        "updated_at": "2023-01-02T00:02:00"
                    }
                ],
                "total": 2,
                "page": 1,
                "page_size": 10,
                "pages": 1
            }
        }