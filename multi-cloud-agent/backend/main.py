from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    status: str
    message: str
    steps: list

@app.post("/prompt", response_model=PromptResponse)
async def handle_prompt(request: PromptRequest):
    # Mock response for now
    return PromptResponse(
        status="success",
        message=f"Received prompt: {request.prompt}",
        steps=[
            {"step": 1, "action": "Parse prompt", "status": "done"},
            {"step": 2, "action": "Identify cloud operation", "status": "pending"}
        ]
    )