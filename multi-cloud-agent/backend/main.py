from fastapi import FastAPI
from pydantic import BaseModel
from intent_extractor import extract_intent
from cloud_handlers import handle_cloud
from knowledge_base import get_operation_doc

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    status: str
    message: str
    steps: list

class KnowledgeRequest(BaseModel):
    cloud: str
    resource: str
    operation: str

class KnowledgeResponse(BaseModel):
    documentation: str

@app.post("/prompt", response_model=PromptResponse)
async def handle_prompt(request: PromptRequest):
    steps = []
    # Step 1: Parse prompt and extract intent
    steps.append({"step": 1, "action": "Parse prompt", "status": "done", "details": request.prompt})
    intent = extract_intent(request.prompt)
    steps.append({"step": 2, "action": "Extract intent", "status": "done", "details": intent})
    # Step 2: Select handler and execute
    if intent['cloud'] and intent['operation'] != 'unknown' and intent['resource'] != 'unknown':
        result = handle_cloud(intent['cloud'], intent['operation'], intent['resource'])
        steps.append({"step": 3, "action": f"Execute {intent['operation']} {intent['resource']} on {intent['cloud']}", "status": "done", "details": result})
        status = "success"
        message = result['result']
    else:
        steps.append({"step": 3, "action": "Execution", "status": "error", "details": "Could not determine intent or operation"})
        status = "error"
        message = "Could not determine intent or operation from prompt."
    return PromptResponse(
        status=status,
        message=message,
        steps=steps
    )

@app.post("/knowledge", response_model=KnowledgeResponse)
async def knowledge(request: KnowledgeRequest):
    doc = get_operation_doc(request.cloud, request.resource, request.operation)
    return KnowledgeResponse(documentation=doc)