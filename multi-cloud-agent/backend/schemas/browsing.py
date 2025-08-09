from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from schemas.base import BaseSchema, BaseResponseSchema

class UpworkJobRequest(BaseSchema):
    """
    Schema for Upwork job application request.
    """
    browser_id: str
    job_url: str
    cover_letter: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "browser_id": "browser_1",
                "job_url": "https://www.upwork.com/jobs/123456",
                "cover_letter": "I am interested in this job..."
            }
        }

class BrowsingRequest(BaseSchema):
    """
    Schema for browsing request.
    """
    url: str
    query: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.example.com",
                "query": "search term"
            }
        }

class BrowsingResponse(BaseResponseSchema):
    """
    Schema for browsing response.
    """
    content: str
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "<html>...</html>",
                "url": "https://www.example.com"
            }
        }

class ToolCallRequest(BaseSchema):
    """
    Schema for tool call request.
    """
    tool_name: str
    params: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "search_web",
                "params": {"query": "example search"}
            }
        }

class FiverrJobRequest(BaseSchema):
    """
    Schema for Fiverr job application request.
    """
    browser_id: str
    job_url: str
    cover_letter: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "browser_id": "browser_1",
                "job_url": "https://www.fiverr.com/jobs/123456",
                "cover_letter": "I am interested in this job..."
            }
        }

class LinkedInJobRequest(BaseSchema):
    """
    Schema for LinkedIn job application request.
    """
    browser_id: str
    job_url: str
    resume_path: str
    cover_letter: str
    phone: str
    profile_name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "browser_id": "browser_1",
                "job_url": "https://www.linkedin.com/jobs/123456",
                "resume_path": "/path/to/resume.pdf",
                "cover_letter": "I am interested in this job...",
                "phone": "+1234567890",
                "profile_name": "John Doe"
            }
        }