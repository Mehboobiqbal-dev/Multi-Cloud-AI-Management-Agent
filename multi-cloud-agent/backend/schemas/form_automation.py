from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from schemas.base import BaseSchema, BaseResponseSchema

class BatchJobRequest(BaseSchema):
    """
    Schema for batch job application request.
    """
    job_urls: List[str]
    platform: str
    browser_id: Optional[str] = None
    profile_name: Optional[str] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_urls": ["https://www.example.com/job/123", "https://www.example.com/job/456"],
                "platform": "linkedin",
                "browser_id": "browser_1",
                "profile_name": "John Doe",
                "additional_params": {
                    "cover_letter": "I am interested in this job...",
                    "resume_path": "/path/to/resume.pdf",
                    "phone": "+1234567890"
                }
            }
        }

class RegistrationRequest(BaseSchema):
    """
    Schema for website registration automation request.
    """
    browser_id: str
    url: str
    form_data: Dict[str, Any]
    submit_selector: Optional[str] = None
    success_indicator: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "browser_id": "browser_1",
                "url": "https://www.example.com/register",
                "form_data": {
                    "username": "johndoe",
                    "email": "john@example.com",
                    "password": "securepassword",
                    "confirm_password": "securepassword"
                },
                "submit_selector": "button[type=submit]",
                "success_indicator": ".success-message"
            }
        }

class LoginAutomationRequest(BaseSchema):
    """
    Schema for website login automation request.
    """
    browser_id: str
    url: str
    username_selector: str
    username: str
    password_selector: str
    password: str
    submit_selector: str
    success_indicator: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "browser_id": "browser_1",
                "url": "https://www.example.com/login",
                "username_selector": "#username",
                "username": "johndoe",
                "password_selector": "#password",
                "password": "securepassword",
                "submit_selector": "button[type=submit]",
                "success_indicator": ".dashboard"
            }
        }