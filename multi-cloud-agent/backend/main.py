from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import List, Dict
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from passlib.context import CryptContext

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import SessionLocal, init_db
from models import User, CloudCredential
from secure import encrypt, decrypt
from gemini import generate_text
from audit import log_audit
from tools import tool_registry
from memory import memory_instance
import json
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
import schemas

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
async def startup_event():
    init_db()

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
        expire = datetime.utcnow() + timedelta(minutes=15)
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
    return await oauth.google.authorize_redirect(request, redirect_uri)

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
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Credential management endpoints (to be filled in next steps)
@app.get('/me', response_model=schemas.User)
async def me(user: schemas.User = Depends(get_current_user)):
    return user

@app.get('/credentials', response_model=List[schemas.Credential])
async def get_credentials(user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = db.query(CloudCredential).filter_by(user_id=user.id).all()
    return creds

@app.post('/credentials', response_model=schemas.Credential)
async def save_credentials(cred_data: schemas.CredentialCreate, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    cred = db.query(CloudCredential).filter_by(user_id=user.id, provider=cred_data.provider).first()
    if not cred:
        cred = CloudCredential(user_id=user.id, provider=cred_data.provider)
    
    update_data = cred_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key not in ["provider"] and value is not None:
            setattr(cred, key, encrypt(value))

    db.add(cred)
    db.commit()
    db.refresh(cred)
    log_audit(db, user.id, f'update_{cred_data.provider}_credentials', 'Credentials updated')
    return cred

# ... cloud operation endpoints will be refactored next ...

@app.post('/prompt')
async def prompt(prompt_req: schemas.PromptRequest, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    prompt_text = prompt_req.prompt
    
    # 1. Search for relevant documents in memory
    retrieved_docs = memory_instance.search(prompt_text)
    context = "\n".join([doc for _, doc in retrieved_docs])

    # 2. Generate Plan with Gemini, including context from memory
    gemini_prompt = f"""
    Based on the following user prompt and conversation history, create a detailed execution plan.
    The plan should be a list of dictionaries, where each dictionary represents a step with 'action' and 'params'.
    Available tools are: {', '.join(tool_registry.get_all_tools().keys())}.
    
    Conversation History:
    {context}
    
    User Prompt: {prompt_text}
    """
    
    try:
        response_text = generate_text(gemini_prompt)
        plan = json.loads(response_text)
    except (json.JSONDecodeError, TypeError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate or parse plan: {e}")

    # 3. Add the current interaction to memory
    memory_instance.add_document(f"User prompt: {prompt_text}\nGenerated plan: {plan}")

    return {"plan": plan}

@app.post('/execute_plan')
async def execute_plan(plan: List[Dict], user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Aggregate user credentials
    creds = db.query(CloudCredential).filter_by(user_id=user.id).all()
    user_creds = {}
    for c in creds:
        if c.provider == 'aws':
            user_creds['aws'] = {
                'access_key': decrypt(c.access_key),
                'secret_key': decrypt(c.secret_key)
            }
        elif c.provider == 'azure':
            user_creds['azure'] = {
                'azure_subscription_id': decrypt(c.azure_subscription_id),
                'azure_client_id': decrypt(c.azure_client_id),
                'azure_client_secret': decrypt(c.azure_client_secret),
                'azure_tenant_id': decrypt(c.azure_tenant_id)
            }
        elif c.provider == 'gcp':
            user_creds['gcp'] = {
                'gcp_project_id': decrypt(c.gcp_project_id),
                'gcp_credentials_json': decrypt(c.gcp_credentials_json)
            }

    execution_steps = []
    for planned_step in plan:
        action = planned_step['action']
        params = planned_step['params']
        
        tool = tool_registry.get_tool(action)
        if not tool:
            execution_steps.append({
                "step": planned_step['step'],
                "action": action,
                "status": "error",
                "details": f"Tool '{action}' not found."
            })
            continue

        try:
            if action == "cloud_operation":
                params["user_creds"] = user_creds
            result = tool.func(**params)
            execution_steps.append({
                "step": planned_step['step'],
                "action": action,
                "status": "done",
                "details": result
            })
        except Exception as e:
            execution_steps.append({
                "step": planned_step['step'],
                "action": action,
                "status": "error",
                "details": str(e)
            })

    log_audit(db, user.id, 'execute_plan', f'Plan: {plan}')

    # Determine overall status
    if all(step['status'] == 'done' for step in execution_steps):
        status = "success"
        message = "Plan executed successfully."
    else:
        status = "error"
        message = "There were errors during plan execution."
        
    return {"status": status, "message": message, "steps": execution_steps}


# CORS and HTTPS enforcement
origins = [
    "http://localhost:3000",
    "https://multi-cloud-ai-management-agent-production-acb4.up.railway.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
if settings.FORCE_HTTPS:
    from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
    app.add_middleware(HTTPSRedirectMiddleware)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get('/healthz')
def healthz():
    return {"status": "ok"}

@app.get('/readyz')
def readyz():
    return {"status": "ready"}
