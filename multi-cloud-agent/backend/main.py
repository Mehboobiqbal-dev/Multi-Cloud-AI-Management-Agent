from fastapi import FastAPI
from pydantic import BaseModel
from intent_extractor import extract_intents
from cloud_handlers import handle_clouds
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
    # Step 1: Parse prompt and extract intents
    steps.append({"step": 1, "action": "Parse prompt", "status": "done", "details": request.prompt})
    intents = extract_intents(request.prompt)
    steps.append({"step": 2, "action": "Extract intents", "status": "done", "details": intents})
    # Step 2: Execute for each cloud
    results = handle_clouds(intents)
    for idx, res in enumerate(results):
        details = res['result']
        status = 'done' if 'result' in details and not details.get('error') else 'error'
        steps.append({
            "step": 3 + idx,
            "action": f"Execute {res['operation']} {res['resource']} on {res['cloud']}",
            "status": status,
            "details": details
        })
    # Aggregate status and message
    if all('result' in r['result'] and not r['result'].get('error') for r in results):
        status = "success"
        message = "; ".join(r['result']['result'] for r in results)
    else:
        status = "error"
        message = "; ".join(r['result'].get('error', r['result'].get('result', 'Unknown error')) for r in results)
    return PromptResponse(
        status=status,
        message=message,
        steps=steps
    )

@app.post("/knowledge", response_model=KnowledgeResponse)
async def knowledge(request: KnowledgeRequest):
    doc = get_operation_doc(request.cloud, request.resource, request.operation)
    return KnowledgeResponse(documentation=doc)