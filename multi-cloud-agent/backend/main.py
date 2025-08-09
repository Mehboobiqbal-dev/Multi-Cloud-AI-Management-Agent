import sys
import os
from dotenv import load_dotenv

load_dotenv()

from core.config import settings

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import List, Dict, Any
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from passlib.context import CryptContext

import time
from core.db import SessionLocal, Base
from core.db import init_db
from models import User, CloudCredential, PlanHistory
from security import encrypt_text as encrypt, decrypt_text as decrypt
from openai import OpenAI

from audit import log_audit
from tools import tool_registry, browsers
from self_learning import SelfLearningCore
import api_integration
import autonomy
import browsing
# Import clear_users module but don't execute code
from clear_users import clear_all_users
import cli
import cloud_handlers
import content_creation
import custom_plugins
import ecommerce
import email_messaging
import form_automation
import gemini
import groq
import intent_extractor
import knowledge_base
import memory
import multilingual
import multimodal
import planner
import scraping_analysis
import security
import social_media
# import voice_control
import universal_assistant
import json
import re

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import schemas
import logging
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi import WebSocket, WebSocketDisconnect

core = SelfLearningCore()

from fastapi.middleware.cors import CORSMiddleware

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def lifespan(app: FastAPI):
    try:
        init_db()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Fatal error during database initialization: {e}", exc_info=True)
        raise
    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error during request to {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "An internal server error occurred."})

@app.exception_handler(FastAPIRequestValidationError)
async def validation_exception_handler(request: Request, exc: FastAPIRequestValidationError):
    logging.warning(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SESSION_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

@app.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )
    
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    return response

@app.get('/login/{provider}')
async def login(request: Request, provider: str):
    if provider not in ['google']:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    redirect_uri = request.url_for('auth', provider=provider)
    return await oauth.google.authorize_redirect(request, str(redirect_uri))

@app.get('/auth/{provider}')
async def auth(request: Request, provider: str, db: Session = Depends(get_db)):
    if provider not in ['google']:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Google login failed: {e}')

    user = db.query(User).filter_by(email=user_info['email']).first()
    if not user:
        user = User(email=user_info['email'], name=user_info.get('name'), google_id=user_info['sub'])
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/")
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=1800, samesite="lax")
    return response

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> schemas.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_from_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db)
) -> schemas.User:
    token = websocket.query_params.get("token")
    if token is None:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    try:
        # The token from the query parameter might be prefixed with "Bearer ", remove it
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
            
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
    except JWTError:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
    return user

# Register universal assistant routes after get_current_user is defined to avoid NameError

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user: schemas.User = Depends(get_current_user_from_ws)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

app.include_router(universal_assistant.router, prefix="/assistant", tags=["assistant"], dependencies=[Depends(get_current_user)])

@app.get('/me', response_model=schemas.User)
async def me(user: schemas.User = Depends(get_current_user)):
    return user

@app.get('/credentials', response_model=List[schemas.CloudCredential])
async def get_credentials(user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = db.query(CloudCredential).filter_by(user_id=user.id).all()
    return creds

@app.post('/credentials', response_model=schemas.CloudCredential)
async def save_credentials(cred_data: schemas.CloudCredentialCreate, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    cred = db.query(CloudCredential).filter_by(user_id=user.id, provider=cred_data.provider).first()
    if not cred:
        cred = CloudCredential(user_id=user.id, provider=cred_data.provider)
    
    update_data = cred_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key not in ["provider"] and value is not None:
            setattr(cred, key, encrypt(value))

    db.add(cred)
    db.commit()
    db.refresh(cred)
    log_audit(db, user.id, f'update_{cred_data.provider}_credentials', 'Credentials updated')
    return cred

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post('/prompt')
@limiter.limit("10/minute")
async def prompt(request: Request, prompt_req: schemas.PromptRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    prompt_text = prompt_req.prompt
    logging.info(f"Received prompt from user {user.id}: '{prompt_text}'")
    
    try:
        memory_instance = memory.get_memory_instance()
        retrieved_docs_tuples = memory_instance.search(prompt_text, k=3)
        context_parts = []
        for _, doc in retrieved_docs_tuples:
            context_parts.append(
                f"---\nPAST INTERACTION:\n"
                f"  - User Prompt: {doc.get('prompt')}\n"
                f"  - My Plan: {json.dumps(doc.get('plan'))}\n"
                f"  - Execution Result: {json.dumps(doc.get('execution_results'))}\n"
                f"  - User Feedback: {doc.get('feedback')}\n"
                f"  - Correction/Reason: {doc.get('correction')}\n---"
            )
        context = "\n\n".join(context_parts)
        logging.info(f"Retrieved {len(retrieved_docs_tuples)} documents from memory to use as context.")
    except Exception as e:
        logging.error(f"Error searching memory: {e}", exc_info=True)
        context = "No past interactions found."

    tool_descriptions = json.dumps(tool_registry.get_all_tools_dict(), indent=2)
    gemini_prompt = f"""
You are a world-class autonomous AI agent IDE. Your primary goal is to create a multi-step execution plan based on a user's request, available tools, past experiences, with autonomy, security, and multilingual support.

**INSTRUCTIONS:**
1. **Analyze and Learn:** ...
2. **Learn from Mistakes:** ...
3. **Think Step-by-Step:** ... Include self-critique steps after key actions using 'ask_user' for internal reflection if needed.
4. **Ask for Clarification:** ...
5. **Security Check:** Before any action requiring credentials, add a step to verify them.
6. **Multilingual:** Detect user language and translate responses if not English.
7. **Autonomy:** Plan for loops where you evaluate progress and adjust.
8. **Formulate a Plan:** ...

**AVAILABLE TOOLS:**
{tool_descriptions}

**EXAMPLE WEB AUTOMATION FLOW:**
This is how you sign up for a newsletter. Notice how the `browser_id` returned by `open_browser` is used in subsequent steps.
USER REQUEST: "Go to example.com/newsletter and sign up with my email, test@example.com."
YOUR PLAN:
{{
    "plan": [
        {{
            "step": 1,
            "action": "open_browser",
            "params": {{"url": "https://example.com/newsletter"}}
        }},
        {{
            "step": 2,
            "action": "fill_form",
            "params": {{"browser_id": "browser_0", "selector": "input[name='email']", "value": "test@example.com"}}
        }},
        {{
            "step": 3,
            "action": "click_button",
            "params": {{"browser_id": "browser_0", "selector": "button[type='submit']"}}
        }},
        {{
            "step": 4,
            "action": "get_page_content",
            "params": {{"browser_id": "browser_0"}}
        }},
        {{
            "step": 5,
            "action": "close_browser",
            "params": {{"browser_id": "browser_0"}}
        }}
    ]
}}

**CONTEXT FROM PAST INTERACTIONS:**
{context}

**CURRENT USER REQUEST:** {prompt_text}

**RESPONSE FORMAT (JSON object with a "plan" key, no markdown):**
"""
    logging.info("Generating plan with LLM...")
    
    try:
        response_text = generate_text(gemini_prompt)
        logging.info(f"LLM raw response: {response_text}")
        
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            plan_text = json_match.group(1)
        else:
            plan_text = response_text

        response_data = json.loads(plan_text)
        plan = response_data.get("plan")

        if not isinstance(plan, list):
            raise json.JSONDecodeError("The 'plan' key must contain a list of steps.", plan_text, 0)

    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        logging.error(f"Failed to generate or parse a valid plan from LLM response: {e}", exc_info=True)
        return {
            "plan": [{"step": 1, "action": "ask_user", "params": {"question": "I had trouble formulating a plan. Could you please rephrase or provide more detail?"}}]
        }
    except Exception as e:
        logging.error(f"An unexpected error occurred during plan generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during plan generation.")

    return {"plan": plan, "prompt": prompt_text}

@app.post('/execute_plan')
@limiter.limit("10/minute")
async def execute_plan(request: Request, exec_req: schemas.PlanExecutionRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    core.log_action('execute_plan', {'prompt': exec_req.prompt})
    try:
        plan = exec_req.plan
        prompt_text = exec_req.prompt
        
        creds = db.query(CloudCredential).filter_by(user_id=user.id).all()
        user_creds = {}
        for c in creds:
            if c.provider == 'aws':
                user_creds['aws'] = {'access_key': decrypt(c.access_key), 'secret_key': decrypt(c.secret_key)}
            elif c.provider == 'azure':
                user_creds['azure'] = {'azure_subscription_id': decrypt(c.azure_subscription_id), 'azure_client_id': decrypt(c.azure_client_id), 'azure_client_secret': decrypt(c.azure_client_secret), 'azure_tenant_id': decrypt(c.azure_tenant_id)}
            elif c.provider == 'gcp':
                 user_creds['gcp'] = {'gcp_project_id': decrypt(c.gcp_project_id), 'gcp_credentials_json': decrypt(c.gcp_credentials_json)}

        execution_steps = []
        for i, planned_step in enumerate(plan):
            action = planned_step.get('action')
            params = planned_step.get('params', {})
            step_num = planned_step.get('step', i + 1)

            if not action:
                execution_steps.append({"step": step_num, "action": "unknown", "status": "error", "details": "Missing 'action' in plan step."})
                continue
            
            if action == "ask_user":
                return {"status": "requires_input", "message": "User input required", "details": params.get("question")}

            tool = tool_registry.get_tool(action)
            if not tool:
                execution_steps.append({"step": step_num, "action": action, "status": "error", "details": f"Tool '{action}' not found in registry."})
                continue

            try:
                logging.info(f"Executing step {step_num}: action='{action}', params={params}")
                if action == "cloud_operation":
                    params["user_creds"] = user_creds
                result = tool.func(**params)
                execution_steps.append({"step": step_num, "action": action, "status": "done", "details": result})
            except Exception as e:
                logging.error(f"Error executing step {step_num} ('{action}'): {e}", exc_info=True)
                execution_steps.append({"step": step_num, "action": action, "status": "error", "details": f"An exception occurred: {str(e)}"})

        overall_status = "error" if any(s['status'] == 'error' for s in execution_steps) else "success"
        
        new_plan_history = PlanHistory(
            user_id=user.id,
            prompt=prompt_text,
            plan=json.dumps(plan),
            status='requires_feedback',
            execution_results=json.dumps(execution_steps)
        )
        db.add(new_plan_history)
        db.commit()
        db.refresh(new_plan_history)

        log_audit(db, user.id, 'execute_plan', f'Plan History ID: {new_plan_history.id}')
        core.post_task_review(prompt_text, overall_status == 'success', {'steps': len(execution_steps)})
    except Exception as e:
        core.log_error(str(e), {'prompt': prompt_text})
        raise
    return {
        "status": overall_status,
        "message": "Plan execution finished. Your feedback is valuable for my improvement.",
        "steps": execution_steps,
        "plan_id": new_plan_history.id,
        "feedback_prompt": f"Did this work as expected? To help me learn, please use the /feedback endpoint with plan_id: {new_plan_history.id} and your feedback ('success' or 'failure')."
    }

@app.post('/feedback')
async def feedback(feedback_req: schemas.FeedbackRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan_history = db.query(PlanHistory).filter(PlanHistory.id == feedback_req.plan_id, PlanHistory.user_id == user.id).first()

    if not plan_history:
        raise HTTPException(status_code=404, detail="Plan history not found for the current user.")
    
    if feedback_req.feedback not in ["success", "failure"]:
        raise HTTPException(status_code=400, detail="Feedback must be either 'success' or 'failure'.")

    plan_history.feedback = feedback_req.feedback
    plan_history.correction = feedback_req.correction
    plan_history.status = feedback_req.feedback
    db.commit()

    try:
        interaction_data = {
            "prompt": plan_history.prompt,
            "plan": json.loads(plan_history.plan),
            "execution_results": json.loads(plan_history.execution_results),
            "feedback": plan_history.feedback,
            "correction": plan_history.correction
        }
        memory_instance.add_document(interaction_data)
        logging.info(f"Added feedback and full interaction for plan {feedback_req.plan_id} to agent's memory.")
    except Exception as e:
        logging.error(f"Error adding feedback to memory for plan {feedback_req.plan_id}: {e}", exc_info=True)
        return {"status": "success", "message": "Feedback recorded, but failed to update my long-term memory."}

    return {"status": "success", "message": "Thank you for the feedback! I've recorded it to improve my future performance."}

@app.get('/healthz')
def healthz():
    return {"status": "ok"}

@app.post('/form/apply_job_upwork')
async def api_apply_job_upwork(request: schemas.UpworkJobRequest, user: schemas.User = Depends(get_current_user)):
    try:
        result = form_automation.apply_job_upwork(
            request.browser_id,
            request.job_url,
            request.cover_letter,
            request.profile_name
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying for Upwork job: {str(e)}")

@app.post('/form/apply_job_fiverr')
async def api_apply_job_fiverr(request: schemas.FiverrJobRequest, user: schemas.User = Depends(get_current_user)):
    try:
        result = form_automation.apply_job_fiverr(
            request.browser_id,
            request.buyer_request_url,
            request.proposal,
            request.price,
            request.profile_name
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying for Fiverr job: {str(e)}")

@app.post('/form/apply_job_linkedin')
async def api_apply_job_linkedin(request: schemas.LinkedInJobRequest, user: schemas.User = Depends(get_current_user)):
    try:
        result = form_automation.apply_job_linkedin(
            request.browser_id,
            request.job_url,
            request.resume_path,
            request.cover_letter,
            request.phone,
            request.profile_name
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying for LinkedIn job: {str(e)}")

@app.post('/form/batch_apply_jobs')
async def api_batch_apply_jobs(request: schemas.BatchJobRequest, user: schemas.User = Depends(get_current_user)):
    try:
        result = form_automation.create_job_application_batch(
            request.job_urls,
            request.platform,
            request.browser_id,
            request.profile_name,
            **request.additional_params
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch job application: {str(e)}")

@app.post('/form/automate_registration')
async def api_automate_registration(request: schemas.RegistrationRequest, user: schemas.User = Depends(get_current_user)):
    try:
        result = form_automation.automate_registration(
            request.browser_id,
            request.url,
            request.form_data,
            request.submit_selector,
            request.success_indicator
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error automating registration: {str(e)}")

@app.post('/form/automate_login')
async def api_automate_login(request: schemas.LoginAutomationRequest, user: schemas.User = Depends(get_current_user)):
    try:
        result = form_automation.automate_login(
            request.browser_id,
            request.url,
            request.username_selector,
            request.username,
            request.password_selector,
            request.password,
            request.submit_selector,
            request.success_indicator
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error automating login: {str(e)}")

@app.post('/call_tool')
async def call_tool(tool_req: schemas.ToolCallRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    tool_name = tool_req.tool_name
    params = tool_req.params
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
    try:
        if tool_name in ['open_browser', 'get_page_content', 'fill_form', 'fill_multiple_fields', 'click_button', 'close_browser', 'search_web',
                        'select_dropdown_option', 'upload_file', 'wait_for_element', 'check_checkbox']:
            result = tool.func(**params)
        else:
            creds = db.query(CloudCredential).filter_by(user_id=user.id).all()
            user_creds = {}
            for c in creds:
                if c.provider == 'aws':
                    user_creds['aws'] = {'access_key': decrypt(c.access_key), 'secret_key': decrypt(c.secret_key)}
                # Add other providers similarly
            params['credentials'] = user_creds.get(tool_name.split('_')[-1], {})
            result = tool.func(**params)
        return {'result': result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")

def generate_text(prompt: str) -> str:
    # Try Gemini first with its internal API key failover
    try:
        return gemini.generate_text(prompt)
    except HTTPException as e:
        # If Gemini fails due to quota or other issues, try Groq as a fallback
        logging.warning(f"Gemini generation failed: {e.detail}. Falling back to Groq.")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return groq.generate_text(prompt)
            except HTTPException as groq_e:
                if groq_e.status_code == 429 and attempt < max_retries - 1:
                    logging.warning(f"Groq 429 on attempt {attempt+1}, retrying immediately")
                else:
                    logging.error(f"Groq generation also failed: {groq_e}")
                    raise HTTPException(status_code=500, detail=f"All LLM providers failed: {str(groq_e)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred with Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected LLM error occurred: {e}")

@app.post('/agent/run', response_model=schemas.AgentRunResponse, tags=["Agent"])
@limiter.limit("5/minute")
async def agent_run(request: Request, agent_req: schemas.AgentStateRequest, user: schemas.User = Depends(get_current_user)):
    core.log_action('agent_run', {'user_input': agent_req.user_input})
    try:
        goal = agent_req.user_input
        max_loops = 3
        history = []

        # Define the agent loop prompt template
        AGENT_LOOP_PROMPT = """
        You are a highly intelligent, self-sufficient AI agent capable of performing any task on the internet autonomously without needing user input. Always think step by step and persist until the goal is achieved. If the goal is null, unclear, or not provided, infer from history or default to useful autonomous tasks like searching the web for trending topics, analyzing information, or performing exploratory actions independently. Never attempt to ask the user for clarification; instead, make reasonable assumptions or choose a default goal.
        
        GOAL: {goal}
        
        HISTORY: {history}
        
        TOOLS: {tools}
        
        Output ONLY a valid JSON object. No other text, no explanations outside the JSON. The JSON must have exactly:
        {{
            "thought": "Your reasoning",
            "action": {{
                "name": "tool_name",
                "params": {{}}
            }}
        }}
        
        For completion, use "finish_task" with {{"final_answer": "result"}}.
        Never use non-existent tools like 'ask_user'. Persist through errors and adapt autonomously.
        """
    
        for i in range(max_loops):
            logging.info(f"--- Agent Loop {i+1} for goal: '{goal}' ---")
            
            # 1. THINK and CHOOSE NEXT ACTION
            history_str = "\n".join([f"  - Step {h['step']}: I used '{h['action']['name']}' which resulted in: '{h['result']}'" for h in history]) if history else "  - No actions taken yet."
            thought = "No thought recorded due to an error."
            prompt = AGENT_LOOP_PROMPT.format(
                goal=goal,
                history=history_str,
                tools=json.dumps(tool_registry.get_all_tools_dict(), indent=2)
            )
            
            try:
                response_text = generate_text(prompt)
                logging.info(f"Agent LLM Response: {response_text}")
                # Extract JSON from the response
                import re
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response_text)
                if json_match:
                    json_string = json_match.group(1)
                    decision_data = json.loads(json_string)
                else:
                    # Fallback if no JSON block is found, try to parse the whole response
                    # This might still fail if the response is not pure JSON
                    decision_data = json.loads(response_text)

                thought = decision_data.get("thought", "No thought provided.")
                action_data = decision_data.get("action", {})
                action_name = action_data.get("name")
                action_params = action_data.get("params", {})
            except (json.JSONDecodeError, AttributeError) as e:
                logging.error(f"Failed to parse agent decision from response: '{response_text}'. Error: {e}", exc_info=True)
                return schemas.AgentRunResponse(status="error", message=f"Agent failed to parse LLM response: '{response_text}'. Last thought was: {thought}", history=history, final_result=None)

            if not action_name or not isinstance(action_params, dict):
                 return schemas.AgentRunResponse(status="error", message=f"Agent generated an invalid action. Last thought: {thought}", history=history, final_result=None)

            # 2. EXECUTE THE CHOSEN ACTION
            logging.info(f"Agent Thought: {thought}")
            logging.info(f"Agent Action: {action_name} with params {action_params}")

            tool = tool_registry.get_tool(action_name)
            if not tool:
                result = f"Error: Tool '{action_name}' not found."
            else:
                try:
                    result = tool.func(**action_params)
                except Exception as e:
                    result = f"Error executing tool '{action_name}': {e}"
            
            # 3. RECORD AND OBSERVE
            history.append({
                "step": i + 1,
                "thought": thought,
                "action": action_data,
                "result": str(result) # Ensure result is a string
            })

            # Self-Critique
            critique_prompt = f"Goal: {goal}\nLast Action Result: {result}\nCritique and suggest improvement."
            critique = generate_text(critique_prompt)
            logging.info(f"Self-Critique: {critique}")

            # 4. CHECK FOR COMPLETION
            if action_name == "finish_task":
                logging.info(f"Agent finished goal: '{goal}'")
                return schemas.AgentRunResponse(status="success", message="Agent completed the goal.", history=history, final_result=result)
            

        logging.warning(f"Agent reached max loops for goal: '{goal}'")
        core.post_task_review(goal, False, {'loops': max_loops})
        return schemas.AgentRunResponse(status="error", message="Agent reached maximum loops without finishing the goal.", history=history, final_result=None)
    except Exception as e:
        core.log_error(str(e), {'goal': goal})
        raise

@app.get('/')
def root():
    return {"message": "Multi-Cloud AI Management API is running!", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
