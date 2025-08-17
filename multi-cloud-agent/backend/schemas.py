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
    email: str
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

class UpworkJobRequest(BaseModel):
    browser_id: str
    job_url: str
    cover_letter: str
    profile_name: Optional[str] = None

class FiverrJobRequest(BaseModel):
    browser_id: str
    buyer_request_url: str
    proposal: str
    price: float
    profile_name: Optional[str] = None

class LinkedInJobRequest(BaseModel):
    browser_id: str
    job_url: str
    resume_path: str
    cover_letter: str
    phone: Optional[str] = None
    profile_name: Optional[str] = None

class BatchJobRequest(BaseModel):
    job_urls: List[str]
    platform: str
    browser_id: str
    profile_name: Optional[str] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class RegistrationRequest(BaseModel):
    browser_id: str
    url: str
    form_data: Dict[str, Any]
    submit_selector: str
    success_indicator: Optional[str] = None

class LoginAutomationRequest(BaseModel):
    browser_id: str
    url: str
    username_selector: str
    username: str
    password_selector: str
    password: str
    submit_selector: str
    success_indicator: Optional[str] = None

class TaskResult(BaseModel):
    id: int
    goal: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    result: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    user_id: int

class TaskStatistics(BaseModel):
    total: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    paused: int = 0
    success_rate: float = 0.0
    average_duration_seconds: float = 0.0
    period_days: int = 30
    start_date: str
    end_date: str
