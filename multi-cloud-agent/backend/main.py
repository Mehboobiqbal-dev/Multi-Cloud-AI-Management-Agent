import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Apply memory optimizations early before importing heavy modules
from core.memory_optimization import apply_memory_optimizations
from core.memory_monitor import start_memory_monitoring, get_memory_stats
from core.memory_efficient_cache import get_data_manager, get_cache_stats, optimize_memory
apply_memory_optimizations()

from core.config import settings
from core.structured_logging import structured_logger, LogContext, operation_context
from core.circuit_breaker import circuit_breaker, CircuitBreakerConfig, CircuitBreakerManager
from core.lazy_imports import lazy_import_decorator, get_lazy_import

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
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
from models import User, CloudCredential, PlanHistory, ChatHistory, AgentSession
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
from task_data_manager import task_manager
from response_formatter import ResponseFormatter
import json
import re
import asyncio
import contextlib

MEMORY_FILE = "./agent_memory.json"

def load_agent_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            try:
                data = json.load(f)
                # Assuming 'knowledge' is the key where documents are stored
                for doc in data.get('knowledge', []):
                    memory.memory_instance.add_document(doc)
                print("Agent memory loaded successfully.")
            except json.JSONDecodeError as e:
                print(f"Error decoding agent memory JSON: {e}")
            except Exception as e:
                print(f"Error loading agent memory: {e}")
    else:
        print("Agent memory file not found. Starting with empty memory.")

def save_agent_memory():
    # Only save agent memory if NO_MEMORY is not set to true
    if not os.getenv('NO_MEMORY', 'false').lower() == 'true':
        with open(MEMORY_FILE, 'w') as f:
            # Assuming documents are stored as a list of dictionaries
            json.dump({"knowledge": memory.memory_instance.documents}, f, indent=2)
        print("Agent memory saved successfully.")
    else:
        print("Agent memory saving disabled via NO_MEMORY environment variable")

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import schemas
from schemas.scraping import ScrapeRequest
import logging
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi import WebSocket, WebSocketDisconnect

core = SelfLearningCore()
circuit_breaker_manager = CircuitBreakerManager()

from fastapi.middleware.cors import CORSMiddleware

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from auth import get_current_user

# Configure logging for production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def lifespan(app: FastAPI):
    try:
        logging.info("Database initialization handled by init_db_script.py.")
        
        # Only load agent memory if NO_MEMORY is not set to true
        if not os.getenv('NO_MEMORY', 'false').lower() == 'true':
            load_agent_memory() # Load memory on startup
            logging.info("Agent memory loaded")
        else:
            logging.info("Agent memory loading disabled via NO_MEMORY environment variable")
        
        # Start memory monitoring for 512MB limit
        start_memory_monitoring()
        logging.info("Memory monitoring started for 512MB limit")
        
        app.state.running = True
    except Exception as e:
        logging.error(f"Fatal error during database initialization: {e}", exc_info=True)
        raise
    yield
    app.state.running = False

app = FastAPI(lifespan=lifespan)

active_connections: Dict[int, WebSocket] = {}

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"],
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
    user_id = user.id
    active_connections[user_id] = websocket
    await websocket.accept()
    try:
        while True:
            # Keep the connection alive, or handle incoming messages if needed
            await websocket.receive_text() # This will block until a message is received or connection closes
    except WebSocketDisconnect:
        del active_connections[user_id]
        print(f"Client {user_id} disconnected")
    except Exception as e:
        if user_id in active_connections:
            del active_connections[user_id]
        logging.error(f"WebSocket error for client {user_id}: {e}", exc_info=True)

app.include_router(universal_assistant.router, prefix="/assistant", tags=["assistant"], dependencies=[Depends(get_current_user)])

# Import and register task routes
from routes.tasks import router as tasks_router
app.include_router(tasks_router, dependencies=[Depends(get_current_user)])

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

@app.post('/scrape')
async def scrape_website(scrape_req: ScrapeRequest, user: schemas.User = Depends(get_current_user)):
    from scraping_analysis import scrape_website_comprehensive
    try:
        result = scrape_website_comprehensive(scrape_req.url)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/prompt')
@circuit_breaker(
    'prompt_generation',
    CircuitBreakerConfig(
        failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
        recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
        expected_exception=Exception,
        name='prompt_generation'
    )
)
@limiter.limit("10/minute")
async def prompt(request: Request, prompt_req: schemas.PromptRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    prompt_text = prompt_req.prompt
    prompt_context = LogContext(
        metadata={
            'user_id': user.id,
            'prompt_length': len(prompt_text),
            'operation_type': 'prompt_generation'
        }
    )
    
    with operation_context('prompt_generation', prompt_context):
        structured_logger.log_tool_execution(
            f"Received prompt from user {user.id}: '{prompt_text}'",
            prompt_context,
            {"prompt": prompt_text}
        )
    
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

        from core.utils import parse_json_tolerant
        response_data = parse_json_tolerant(plan_text)
        plan = response_data.get("plan")

        if not isinstance(plan, list):
            raise json.JSONDecodeError("The 'plan' key must contain a list of steps.", plan_text, 0)

    except (json.JSONDecodeError, TypeError, AttributeError, ValueError) as e:
        logging.error(f"Failed to generate or parse a valid plan from LLM response: {e}", exc_info=True)
        return {
            "plan": [{"step": 1, "action": "ask_user", "params": {"question": "I had trouble formulating a plan. Could you please rephrase or provide more detail?"}}]
        }
    except Exception as e:
        logging.error(f"An unexpected error occurred during plan generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during plan generation.")

    return {"plan": plan, "prompt": prompt_text}

@app.post('/execute_plan')
@circuit_breaker(
    'plan_execution',
    CircuitBreakerConfig(
        failure_threshold=getattr(settings, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5),
        recovery_timeout=float(getattr(settings, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60.0)),
        expected_exception=Exception,
        name='plan_execution'
    )
)
@limiter.limit("10/minute")
async def execute_plan(request: Request, exec_req: schemas.PlanExecutionRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    core.log_action('execute_plan', {'prompt': exec_req.prompt})
    execution_context = LogContext(
        metadata={
            'user_id': user.id,
            'plan_steps': len(exec_req.plan),
            'operation_type': 'plan_execution'
        }
    )
    
    try:
        with operation_context('execute_plan', execution_context):
            plan = exec_req.plan
            prompt_text = exec_req.prompt
            
            structured_logger.log_tool_execution(
                f"Executing plan with {len(plan)} steps for user {user.id}",
                execution_context,
                {"plan_steps": len(plan), "prompt": prompt_text}
            )
        
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
        memory_instance = memory.get_memory_instance()
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
    try:
        # Get circuit breaker statuses
        circuit_breaker_status = {
            name: str(cb.state) for name, cb in circuit_breaker_manager.circuit_breakers.items()
        }
        
        # Get memory statistics
        memory_stats = get_memory_stats()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "circuit_breakers": circuit_breaker_status,
            "performance_monitoring": getattr(settings, 'ENABLE_PERFORMANCE_MONITORING', False),
            "memory": memory_stats
        }
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get('/memory/stats')
async def get_memory_statistics():
    """Get detailed memory usage statistics and monitoring data."""
    try:
        memory_stats = get_memory_stats()
        cache_stats = get_cache_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "memory": memory_stats,
                "caches": cache_stats
            }
        }
    except Exception as e:
        logging.error(f"Failed to get memory stats: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

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
    """
    Generate text using Gemini API with built-in failover across multiple API keys.
    """
    try:
        return gemini.generate_text(prompt)
    except HTTPException as e:
        # Re-raise the HTTPException with appropriate error details
        logging.error(f"Gemini generation failed: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"An unexpected error occurred with Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

@app.post('/agent/run', response_model=schemas.AgentRunResponse, tags=["Agent"])
@limiter.limit("5/minute")
async def agent_run(request: Request, agent_req: schemas.AgentStateRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    core.log_action('agent_run', {'user_input': agent_req.user_input})
    user_id = user.id
    websocket = active_connections.get(user_id)
    
    # Add current goal to memory only if provided (avoid adding None during resume)
    if agent_req.user_input:
        memory.memory_instance.add_document({"type": "user_goal", "content": agent_req.user_input, "timestamp": datetime.now().isoformat()})
        save_agent_memory()
    
    # Retrieve relevant context from memory if input provided
    if agent_req.user_input:
        relevant_context = memory.memory_instance.search(agent_req.user_input, k=5) # Get top 5 relevant documents
        context_str = "\n".join([json.dumps(doc) for _, doc in relevant_context])
        if context_str:
            print(f"Retrieved context from memory: {context_str}")

    async def send_log(message: str):
        if websocket:
            try:
                await websocket.send_json({"topic": "agent_updates", "payload": {"log": message}})
            except RuntimeError as e:
                logging.warning(f"Could not send log to WebSocket for user {user_id}: {e}")
        else:
            logging.warning(f"No active WebSocket connection for user {user_id} to send log: {message}")

    try:
        # Ensure we have a run_id to persist and resume the session
        run_id = agent_req.run_id
        if not run_id:
            return schemas.AgentRunResponse(status="error", message="run_id is required to start or resume an agent run.", history=[], final_result=None)

        # Load or create AgentSession
        session_obj = db.query(AgentSession).filter(AgentSession.run_id == run_id, AgentSession.user_id == user_id).first()
        if not session_obj:
            if not agent_req.user_input:
                return schemas.AgentRunResponse(status="error", message="No existing session for run_id and no user_input provided to start a new session.", history=[], final_result=None)
            session_obj = AgentSession(
                user_id=user_id,
                run_id=run_id,
                goal=agent_req.user_input,
                status='running',
                current_step=0,
                history=json.dumps([])
            )
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)

        # Establish goal and prior history from session
        goal = agent_req.user_input or session_obj.goal
        max_loops = 50  # Increased to allow more attempts
        try:
            history = json.loads(session_obj.history) if session_obj.history else []
        except Exception:
            history = []

        await send_log(f"Agent run started for goal: {goal} (run_id={run_id}, resumed_steps={session_obj.current_step})")

        # Helper: infer latest browser_id from history or currently open browsers
        def infer_browser_id_from_history(hist: List[Dict[str, Any]]) -> str:
            import re as _re
            # Scan history backwards for an explicit browser_id or open_browser result
            for h in reversed(hist):
                try:
                    # Check prior action params first
                    act = h.get("action", {})
                    params = act.get("params", {})
                    bid = params.get("browser_id")
                    if isinstance(bid, str) and bid.startswith("browser_"):
                        return bid
                    # Then check result text for the standard open_browser message
                    res = h.get("result", "")
                    if isinstance(res, str):
                        m = _re.search(r"Browser opened with ID: (browser_\\d+)", res)
                        if m:
                            return m.group(1)
                except Exception:
                    continue
            # Fallback to the most recent live browser from the shared browsers dict
            try:
                if browsers:
                    ids = list(browsers.keys())
                    ids.sort(key=lambda x: int(x.split('_')[-1]))
                    return ids[-1]
            except Exception:
                pass
            return None

        # Define the agent loop prompt template
        AGENT_LOOP_PROMPT = """
        You are Elch, a highly intelligent, self-sufficient AI agent capable of performing any task on the internet autonomously. Always think step by step and persist until the goal is achieved. If the goal is null, unclear, or not provided, infer from history or choose a reasonable default goal. Do not ask for generic clarifications; instead, proceed with reasonable assumptions. Only ask the user when absolutely necessary for credentials or one-time secrets that are required to proceed (e.g., login email/password, 2FA codes), using the special action "request_credentials".
        If an action fails, analyze the error message from history and try an alternative strategy (e.g., waiting, using alternative selectors, reloading the page, or using different tools). Continue iterating until "finish_task".
        For any browser-related tool (e.g., get_page_content, fill_form, fill_multiple_fields, click_button, submit_form, close_browser, wait_for_element, select_dropdown_option, upload_file, check_checkbox), you MUST include the "browser_id" parameter. Infer it from the most recent open_browser result in history like "Browser opened with ID: browser_X". If you can't find it explicitly, assume the latest browser_X used in history.
        
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
        Use "request_credentials" only when authentication credentials are absolutely required to continue. Persist through errors and adapt autonomously for all other scenarios.
        """
    
        # Continue from previous step count
        step_offset = int(session_obj.current_step or 0)
        for i in range(max_loops):
            await send_log(f"--- Agent Loop {step_offset + i + 1} for goal: '{goal}' ---")
            
            # 1. THINK and CHOOSE NEXT ACTION
            history_str = "\n".join([f"  - Step {h['step']}: I used '{h['action']['name']}' which resulted in: '{h['result']}'" for h in history]) if history else "  - No actions taken yet."
            # Build the prompt for the next action
            prompt = AGENT_LOOP_PROMPT.format(
                goal=goal,
                history=history_str,
                tools=json.dumps(tool_registry.get_all_tools_dict(), indent=2)
            )
            # Ensure we have a safe default thought in case parsing fails
            thought = "No thought recorded due to an error."
            try:
                await send_log(f"Generating next action with LLM...")
                response_text = generate_text(prompt)
                await send_log(f"LLM Response: {response_text[:200]}...") # Log first 200 chars
                # Extract JSON from the response with tolerant parsing
                from core.utils import parse_json_tolerant
                logging.info(f"Attempting to parse agent decision from response: {response_text[:200]}...")
                decision_data = parse_json_tolerant(response_text)

                thought = decision_data.get("thought", "No thought provided.")
                action_data = decision_data.get("action", {})
                action_name = action_data.get("name")
                action_params = action_data.get("params", {})
            except (json.JSONDecodeError, AttributeError, ValueError) as e:
                logging.error(f"Failed to parse agent decision from response: '{response_text}'. Error: {e}", exc_info=True)
                # Mark session as failed for this attempt, but keep history
                session_obj.status = 'failed'
                session_obj.history = json.dumps(history)
                db.commit()
                return schemas.AgentRunResponse(status="error", message=f"Agent failed to parse LLM response: '{response_text}'. Last thought was: {thought}", history=history, final_result=None)

            if not action_name or not isinstance(action_params, dict):
                session_obj.status = 'failed'
                session_obj.history = json.dumps(history)
                db.commit()
                return schemas.AgentRunResponse(status="error", message=f"Agent generated an invalid action. Last thought: {thought}", history=history, final_result=None)

            # 2. EXECUTE THE CHOSEN ACTION
            await send_log(f"Agent Thought: {thought}")
            await send_log(f"Agent Action: {action_name} with params {action_params}")

            tool = tool_registry.get_tool(action_name)
            if not tool:
                result = f"Error: Tool '{action_name}' not found."
                await send_log(result)
            else:
                # Ensure required browser_id is present for browser tools
                browser_required_tools = {
                    'get_page_content', 'fill_form', 'fill_multiple_fields', 'click_button', 'close_browser',
                    'submit_form', 'wait_for_element', 'select_dropdown_option', 'upload_file', 'check_checkbox'
                }
                try:
                    if action_name in browser_required_tools and 'browser_id' not in action_params:
                        inferred_id = infer_browser_id_from_history(history)
                        if inferred_id:
                            action_params['browser_id'] = inferred_id
                            await send_log(f"Inferred browser_id '{inferred_id}' for action '{action_name}' from history.")
                    
                    # Filter out invalid parameters for specific tools
                    tool_param_filters = {
                        'open_browser': ['url', 'max_retries', 'retry_delay'],
                        'get_page_content': ['browser_id'],
                        'fill_form': ['browser_id', 'selector', 'value', 'wait_timeout'],
                        'click_button': ['browser_id', 'selector'],
                        'close_browser': ['browser_id'],
                        'submit_form': ['browser_id', 'selector'],
                        'wait_for_element': ['browser_id', 'selector', 'timeout'],
                        'search_web': ['query', 'engine']
                    }
                    
                    if action_name in tool_param_filters:
                        valid_param_names = tool_param_filters[action_name]
                        valid_params = {k: v for k, v in action_params.items() if k in valid_param_names}
                        if len(valid_params) != len(action_params):
                            removed_params = set(action_params.keys()) - set(valid_params.keys())
                            await send_log(f"Removed invalid parameters for {action_name}: {removed_params}")
                            action_params = valid_params
                    
                    # Add timeout for browser operations to prevent hanging
                    import asyncio
                    import concurrent.futures
                    
                    if action_name in browser_required_tools:
                        # Execute browser operations with extended timeout for form operations
                        timeout_duration = 60 if action_name in ['fill_multiple_fields', 'fill_form'] else 30
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(tool.func, **action_params)
                            try:
                                result = future.result(timeout=timeout_duration)
                            except concurrent.futures.TimeoutError:
                                await send_log(f"Browser operation '{action_name}' timed out after {timeout_duration} seconds")
                                # Try to continue with a partial success message instead of complete failure
                                if action_name in ['fill_multiple_fields', 'fill_form']:
                                    result = f"Form filling operation timed out but may have partially completed. Continuing to next step."
                                else:
                                    result = f"Error: Browser operation '{action_name}' timed out. This may be due to GPU/WebGL issues."
                    else:
                        result = tool.func(**action_params)
                    
                    await send_log(f"Action Result: {str(result)[:200]}...") # Log first 200 chars
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Check for GPU/WebGL related errors
                    gpu_errors = ['gpu stall', 'webgl', 'opengl', 'graphics', 'gpu driver', 'gl driver']
                    is_gpu_error = any(gpu_err in error_str for gpu_err in gpu_errors)
                    
                    if is_gpu_error:
                        await send_log(f"Detected GPU/WebGL error in '{action_name}': {e}")
                        await send_log("This is likely due to browser GPU acceleration issues. The browser configuration has been updated to disable GPU acceleration.")
                        result = f"GPU/WebGL Error in '{action_name}': Browser may need restart with updated configuration. Error: {e}"
                    else:
                        # Attempt a one-time retry if browser_id seems to be the issue
                        needs_browser = ("browser_id" in error_str) or ("missing 1 required positional argument" in error_str)
                        if action_name in browser_required_tools and ('browser_id' not in action_params or needs_browser):
                            try:
                                inferred_id = infer_browser_id_from_history(history)
                                if inferred_id and action_params.get('browser_id') != inferred_id:
                                    action_params['browser_id'] = inferred_id
                                    await send_log(f"Retrying '{action_name}' with inferred browser_id '{inferred_id}' due to error: {e}")
                                    
                                    # Retry with timeout for browser operations
                                    if action_name in browser_required_tools:
                                        timeout_duration = 60 if action_name in ['fill_multiple_fields', 'fill_form'] else 30
                                        with concurrent.futures.ThreadPoolExecutor() as executor:
                                            future = executor.submit(tool.func, **action_params)
                                            try:
                                                result = future.result(timeout=timeout_duration)
                                            except concurrent.futures.TimeoutError:
                                                if action_name in ['fill_multiple_fields', 'fill_form']:
                                                    result = f"Form filling retry timed out but may have partially completed. Continuing to next step."
                                                else:
                                                    result = f"Error: Retry of '{action_name}' timed out after {timeout_duration} seconds"
                                    else:
                                        result = tool.func(**action_params)
                                    
                                    await send_log(f"Action Result (after retry): {str(result)[:200]}...")
                                else:
                                    raise e
                            except Exception as e2:
                                core.log_error(str(e2), {'goal': goal, 'action': action_name, 'params': action_params})
                                result = f"Error executing tool '{action_name}': {e2}"
                                await send_log(result)
                        else:
                            core.log_error(str(e), {'goal': goal, 'action': action_name, 'params': action_params})
                            result = f"Error executing tool '{action_name}': {e}"
                            await send_log(result)
            
            # 3. RECORD AND OBSERVE
            step_number = step_offset + i + 1
            history.append({
                "step": step_number,
                "thought": thought,
                "action": action_data,
                "result": str(result) # Ensure result is a string
            })
            # Persist session progress after each step
            session_obj.current_step = step_number
            session_obj.history = json.dumps(history)
            session_obj.status = 'running'
            db.commit()

            # Self-Critique
            critique_prompt = f"Goal: {goal}\nLast Action Result: {result}\nCritique and suggest improvement."
            critique = generate_text(critique_prompt)
            await send_log(f"Self-Critique: {critique[:200]}...") # Log first 200 chars

            # 4. CHECK FOR COMPLETION OR USER INPUT NEEDED
            if action_name == "request_credentials" or action_name == "ask_user":
                # Pause the agent and request user input
                assistance_message = action_params.get("message", 
                    action_params.get("question", 
                        "Please provide the required credentials or information to continue."))
                
                await send_log(f"Agent requires user input: {assistance_message}")
                await send_log(json.dumps({
                    "topic": "agent_updates", 
                    "payload": {
                        "status": "requires_input", 
                        "data": {
                            "message": assistance_message,
                            "request_type": action_name,
                            "run_id": session_obj.run_id
                        }
                    }
                }))
                
                session_obj.status = 'requires_input'
                session_obj.awaiting_assistance = True
                session_obj.assistance_request = assistance_message
                session_obj.history = json.dumps(history)
                db.commit()
                
                # Format structured response
                formatted_response = ResponseFormatter.format_agent_response(
                    status="requires_input",
                    message=assistance_message,
                    history=history,
                    final_result=None,
                    goal=goal,
                    current_step=step_number
                )
                
                return schemas.AgentRunResponse(
                    status="requires_input", 
                    message=formatted_response['content'], 
                    history=history, 
                    final_result=None
                )
            
            if action_name == "finish_task":
                await send_log(f"Agent finished goal: '{goal}'")
                
                # Format structured completion response
                formatted_response = ResponseFormatter.format_agent_response(
                    status="success",
                    message="Agent completed the goal successfully.",
                    history=history,
                    final_result=result,
                    goal=goal,
                    current_step=step_number
                )
                
                # Send structured websocket update
                completion_notification = ResponseFormatter.format_task_completion_notification(
                    goal=goal,
                    result=result,
                    history=history
                )
                
                await send_log(json.dumps({
                    "topic": "agent_updates", 
                    "payload": {
                        "status": "complete", 
                        "data": {
                            "final_result": result,
                            "formatted_response": formatted_response,
                            "notification": completion_notification
                        }
                    }
                }))
                
                session_obj.status = 'completed'
                session_obj.history = json.dumps(history)
                db.commit()
                
                return schemas.AgentRunResponse(
                    status="success", 
                    message=formatted_response['content'], 
                    history=history, 
                    final_result=result
                )
            

        await send_log(f"Agent reached max loops for goal: '{goal}'")
        core.post_task_review(goal, False, {'loops': max_loops})
        
        # Format structured response for max loops reached
        formatted_response = ResponseFormatter.format_agent_response(
            status="paused",
            message="Agent reached maximum loops without finishing the goal. The task has been paused and can be resumed.",
            history=history,
            final_result=None,
            goal=goal,
            current_step=len(history)
        )
        
        # Keep session resumable
        session_obj.status = 'paused'
        session_obj.history = json.dumps(history)
        db.commit()
        
        await send_log(json.dumps({
            "topic": "agent_updates", 
            "payload": {
                "status": "paused", 
                "data": {
                    "message": "Agent reached maximum loops without finishing the goal. Call /agent/run again with the same run_id to resume.",
                    "formatted_response": formatted_response,
                    "resumable": True,
                    "run_id": session_obj.run_id
                }
            }
        }))
        
        return schemas.AgentRunResponse(
            status="paused", 
            message=formatted_response['content'], 
            history=history, 
            final_result=None
        )
    except Exception as e:
        error_message = f"An unexpected error occurred during agent run: {e}"
        logging.error(error_message, exc_info=True)
        core.log_error(str(e), {'goal': agent_req.user_input})
        # Try to update session status if possible
        try:
            if 'session_obj' in locals() and session_obj:
                session_obj.status = 'failed'
                session_obj.history = json.dumps(history if 'history' in locals() else [])
                db.commit()
        except Exception:
            pass
        await send_log(error_message)
        await send_log(json.dumps({"topic": "agent_updates", "payload": {"status": "error", "data": {"message": error_message}}}))
        raise

@app.get('/')
def root():
    return {"message": "Multi-Cloud AI Management API is running!", "status": "healthy"}

@app.get('/chat/history')
async def get_chat_history(user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(ChatHistory).filter(ChatHistory.user_id == user.id).order_by(ChatHistory.timestamp.asc()).all()
    return [{
        "id": m.id,
        "sender": m.sender,
        "message": m.message,
        "message_type": m.message_type,
        "agent_run_id": m.agent_run_id,
        "timestamp": m.timestamp.isoformat()
    } for m in messages]

@app.post('/chat/message')
async def post_chat_message(payload: Dict[str, Any], user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = payload.get('message')
    message_type = payload.get('message_type', 'text')
    agent_run_id = payload.get('agent_run_id')
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Ensure the message is a string before saving
    if isinstance(message, dict):
        message_str = json.dumps(message)
    else:
        message_str = str(message)

    chat = ChatHistory(user_id=user.id, sender='user', message=message_str, message_type=message_type, agent_run_id=agent_run_id)
    db.add(chat)
    db.commit()
    # Forward to WebSocket subscribers if present
    ws = active_connections.get(user.id)
    if ws:
        try:
            await ws.send_json({"topic": "chat", "payload": {"sender": "user", "message": message, "message_type": message_type, "agent_run_id": agent_run_id}})
        except Exception:
            pass
    return {"status": "ok"}

@app.get('/tasks/results')
async def get_task_results(user: schemas.User = Depends(get_current_user), limit: int = 50, offset: int = 0):
    """Get paginated list of task results for the current user"""
    try:
        results = task_manager.get_task_results(user_id=user.id, limit=limit, offset=offset)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get('/tasks/statistics')
async def get_task_statistics(user: schemas.User = Depends(get_current_user)):
    """Get task statistics for the current user"""
    try:
        stats = task_manager.get_task_statistics(user_id=user.id)
        return {"success": True, "statistics": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get('/tasks/scraping')
async def get_scraping_results(user: schemas.User = Depends(get_current_user), limit: int = 20, offset: int = 0):
    """Get paginated list of scraping results for the current user"""
    try:
        results = task_manager.get_scraping_results(user_id=user.id, limit=limit, offset=offset)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get('/tasks/{task_id}')
async def get_task_details(task_id: str, user: schemas.User = Depends(get_current_user)):
    """Get detailed information about a specific task"""
    try:
        task_details = task_manager.get_task_by_id(task_id=task_id, user_id=user.id)
        if task_details:
            return {"success": True, "task": task_details}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        return {"success": False, "error": str(e)}

# Modify websocket chat endpoint to accept run_id and assistance
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, user: schemas.User = Depends(get_current_user_from_ws), db: Session = Depends(get_db)):
    user_id = user.id
    active_connections[user_id] = websocket
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message")
            message_type = message_data.get("message_type", "text")
            agent_run_id = message_data.get("agent_run_id")
            if not message:
                continue
            
            # Ensure message is a string before saving
            if isinstance(message, dict):
                message_str = json.dumps(message)
            else:
                message_str = str(message)

            # Save user message to chat history
            user_message = ChatHistory(user_id=user_id, sender="user", message=message_str, message_type=message_type, agent_run_id=agent_run_id)
            db.add(user_message)
            db.commit()
            # Add message to memory if available
            try:
                memory.memory_instance.add_document({"type": "chat", "sender": "user", "message": message, "agent_run_id": agent_run_id, "timestamp": datetime.now().isoformat()})
            except Exception:
                pass
            # Echo back to client and notify agent listeners
            await websocket.send_json({"sender": "user", "text": message, "message_type": message_type, "agent_run_id": agent_run_id})
            ws_agent = active_connections.get(user_id)
            if ws_agent and ws_agent is not websocket:
                try:
                    await ws_agent.send_json({"topic": "chat", "payload": {"sender": "user", "message": message, "message_type": message_type, "agent_run_id": agent_run_id}})
                except Exception:
                    pass
    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]
        print(f"Client {user_id} disconnected from chat")
    except Exception as e:
        if user_id in active_connections:
            del active_connections[user_id]
        logging.error(f"WebSocket chat error for client {user_id}: {e}", exc_info=True)

@app.post('/tasks/{task_id}/chat')
async def chat_with_scraped_content(task_id: str, message: Dict[str, str], user: schemas.User = Depends(get_current_user)):
    """Chat with AI about scraped content"""
    try:
        # Get scraped content from database
        scraped_data = task_manager.get_scraped_content(task_id)
        if not scraped_data:
            raise HTTPException(status_code=404, detail="Scraped content not found")
        
        # Parse the full scraped content
        full_content = json.loads(scraped_data.get('full_scraped_content', '{}'))
        
        # Extract relevant content for AI context
        context_data = {
            'url': scraped_data.get('url', ''),
            'title': scraped_data.get('title', ''),
            'text_content': full_content.get('data', {}).get('text_content', {}),
            'metadata': full_content.get('data', {}).get('metadata', {}),
            'statistics': full_content.get('statistics', {})
        }
        
        # Create AI prompt with context
        user_message = message.get('message', '')
        system_prompt = f"""You are an AI assistant helping analyze scraped web content. 
        
Content Context:
        - URL: {context_data['url']}
        - Title: {context_data['title']}
        - Word Count: {context_data['statistics'].get('word_count', 0)}
        - Page Size: {context_data['statistics'].get('page_size_chars', 0)} characters
        
Text Content Summary:
{json.dumps(context_data['text_content'], indent=2)[:2000]}...
        
Please answer the user's question about this content."""
        
        # Use OpenAI to generate response
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "success": True,
            "response": ai_response,
            "context": {
                "url": context_data['url'],
                "title": context_data['title'],
                "word_count": context_data['statistics'].get('word_count', 0)
            }
        }
        
    except Exception as e:
        structured_logger.error(f"Error in AI chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")

@app.get('/tasks/{task_id}/download')
async def download_scraped_content(task_id: str, format: str = 'json', user: schemas.User = Depends(get_current_user)):
    """Download scraped content in various formats"""
    try:
        # Get scraped content from database
        scraped_data = task_manager.get_scraped_content(task_id)
        if not scraped_data:
            raise HTTPException(status_code=404, detail="Scraped content not found")
        
        # Parse the full scraped content
        full_content = json.loads(scraped_data.get('full_scraped_content', '{}'))
        
        if format.lower() == 'json':
            from fastapi.responses import Response
            return Response(
                content=json.dumps(full_content, indent=2, ensure_ascii=False),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=scraped_content_{task_id}.json"}
            )
        
        elif format.lower() == 'txt':
            # Extract text content
            text_content = full_content.get('data', {}).get('text_content', {})
            text_output = f"Title: {text_content.get('title', '')}\n\n"
            
            # Add headings
            headings = text_content.get('headings', [])
            if headings:
                text_output += "Headings:\n"
                for heading in headings:
                    text_output += f"- {heading}\n"
                text_output += "\n"
            
            # Add paragraphs
            paragraphs = text_content.get('paragraphs', [])
            if paragraphs:
                text_output += "Content:\n"
                for para in paragraphs:
                    text_output += f"{para}\n\n"
            
            from fastapi.responses import Response
            return Response(
                content=text_output,
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename=scraped_content_{task_id}.txt"}
            )
        
        elif format.lower() == 'csv':
            import csv
            from io import StringIO
            
            # Create CSV with structured data
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Type', 'Content'])
            
            # Write title
            text_content = full_content.get('data', {}).get('text_content', {})
            if text_content.get('title'):
                writer.writerow(['Title', text_content['title']])
            
            # Write headings
            for heading in text_content.get('headings', []):
                writer.writerow(['Heading', heading])
            
            # Write paragraphs
            for para in text_content.get('paragraphs', []):
                writer.writerow(['Paragraph', para])
            
            # Write links
            links = full_content.get('data', {}).get('links', [])
            for link in links:
                writer.writerow(['Link', f"{link.get('text', '')} - {link.get('url', '')}"]) 
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=scraped_content_{task_id}.csv"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'json', 'txt', or 'csv'")
            
    except Exception as e:
        structured_logger.error(f"Error downloading content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    # Disable reload in production for better performance and stability
    reload = os.environ.get("ENVIRONMENT", "development") == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
