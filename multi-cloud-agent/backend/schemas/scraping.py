from pydantic import BaseModel, Field

class ScrapeRequest(BaseModel):
    url: str = Field(..., description="The URL to scrape")