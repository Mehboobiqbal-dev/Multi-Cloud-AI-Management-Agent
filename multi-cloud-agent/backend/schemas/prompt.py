from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

from schemas.base import BaseSchema, BaseResponseSchema

class PromptRequest(BaseSchema):
    """
    Schema for prompt request.
    """
    prompt: str = Field(..., min_length=1, max_length=2000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a VM in AWS and install nginx"
            }
        }

class Step(BaseSchema):
    """
    Schema for a single step in a plan.
    """
    step: int
    action: str
    status: str
    details: dict | str
    
    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "action": "create_vm",
                "status": "completed",
                "details": {"instance_id": "i-1234567890abcdef0"}
            }
        }

class PromptResponse(BaseResponseSchema):
    """
    Schema for prompt response.
    """
    status: str
    message: str
    steps: List[Step]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Plan created successfully",
                "steps": [
                    {
                        "step": 1,
                        "action": "create_vm",
                        "status": "completed",
                        "details": {"instance_id": "i-1234567890abcdef0"}
                    }
                ]
            }
        }

class PlanExecutionRequest(BaseSchema):
    """
    Schema for plan execution request.
    """
    prompt: str
    plan: List[Dict[str, Any]]
    user_input: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a VM in AWS and install nginx",
                "plan": [
                    {
                        "step": 1,
                        "action": "create_vm",
                        "params": {"instance_type": "t2.micro"}
                    }
                ],
                "user_input": "Yes, proceed with the plan"
            }
        }

class AgentStateRequest(BaseSchema):
    """
    Schema for agent state request.
    """
    run_id: str
    user_input: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "1234567890",
                "user_input": "Yes, proceed with the plan"
            }
        }

class AgentRunResponse(BaseResponseSchema):
    """
    Schema for agent run response.
    """
    status: str
    message: str
    final_result: Optional[str] = None
    history: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Elch has executed the plan successfully",
                "final_result": "VM created and nginx installed",
                "history": [
                    {
                        "step": 1,
                        "action": "create_vm",
                        "status": "completed",
                        "details": {"instance_id": "i-1234567890abcdef0"}
                    }
                ]
            }
        }

class FeedbackRequest(BaseSchema):
    """
    Schema for feedback request.
    """
    plan_id: int
    feedback: str 
    correction: Optional[str] = None
    new_plan: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": 1,
                "feedback": "positive",
                "correction": None,
                "new_plan": None
            }
        }