from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None
    google_id: Optional[str] = None

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class CredentialBase(BaseModel):
    provider: str

class CredentialCreate(CredentialBase):
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    azure_subscription_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    gcp_project_id: Optional[str] = None
    gcp_credentials_json: Optional[str] = None

class Credential(CredentialBase):
    id: int
    provider: str

    class Config:
        from_attributes = True

class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)

class PlanExecutionRequest(BaseModel):
    prompt: str
    plan: List[Dict[str, Any]]
    user_input: Optional[str] = None

class FeedbackRequest(BaseModel):
    plan_id: int
    feedback: str 
    correction: Optional[str] = None
    new_plan: Optional[List[Dict[str, Any]]] = None

class Step(BaseModel):
    step: int
    action: str
    status: str
    details: dict | str

class PromptResponse(BaseModel):
    status: str
    message: str
    steps: List[Step]

class LoginRequest(BaseModel):
    username: str
    password: str

class AgentStateRequest(BaseModel):
    run_id: str
    user_input: Optional[str] = None

class AgentRunResponse(BaseModel):
    status: str
    message: str
    final_result: Optional[str] = None
    history: List[Dict[str, Any]]

class PlanHistoryBase(BaseModel):
    prompt: str
    plan: str
    status: str

class PlanHistoryCreate(PlanHistoryBase):
    pass

class PlanHistory(PlanHistoryBase):
    id: int
    user_id: int
    timestamp: str

    class Config:
        from_attributes = True

class ToolCallRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any]
