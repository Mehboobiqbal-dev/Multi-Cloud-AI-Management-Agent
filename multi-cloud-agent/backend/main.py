from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from db import SessionLocal, init_db
from models import User, CloudCredential
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SESSION_SECRET', 'devsecret'))

init_db()

oauth = OAuth(Config(environ=os.environ))
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth')
async def auth(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)
    if not user_info:
        raise HTTPException(status_code=400, detail='Google login failed')
    # Find or create user
    user = db.query(User).filter_by(email=user_info['email']).first()
    if not user:
        user = User(email=user_info['email'], name=user_info.get('name'), google_id=user_info['sub'])
        db.add(user)
        db.commit()
        db.refresh(user)
    request.session['user_id'] = user.id
    return RedirectResponse(url='/')

@app.get('/logout')
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/')

# Dependency to get current user
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Not authenticated')
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return user

# Credential management endpoints (to be filled in next steps)
@app.get('/me')
async def me(user: User = Depends(get_current_user)):
    return {'email': user.email, 'name': user.name}

@app.get('/credentials')
async def get_credentials(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = db.query(CloudCredential).filter_by(user_id=user.id).all()
    return [
        {
            'provider': c.provider,
            'access_key': c.access_key,
            'azure_subscription_id': c.azure_subscription_id,
            'gcp_project_id': c.gcp_project_id
        } for c in creds
    ]

@app.post('/credentials')
async def save_credentials(data: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    provider = data.get('provider')
    cred = db.query(CloudCredential).filter_by(user_id=user.id, provider=provider).first()
    if not cred:
        cred = CloudCredential(user_id=user.id, provider=provider)
    # Update fields based on provider
    if provider == 'aws':
        cred.access_key = data.get('access_key')
        cred.secret_key = data.get('secret_key')
    elif provider == 'azure':
        cred.azure_subscription_id = data.get('azure_subscription_id')
        cred.azure_client_id = data.get('azure_client_id')
        cred.azure_client_secret = data.get('azure_client_secret')
        cred.azure_tenant_id = data.get('azure_tenant_id')
    elif provider == 'gcp':
        cred.gcp_project_id = data.get('gcp_project_id')
        cred.gcp_credentials_json = data.get('gcp_credentials_json')
    db.add(cred)
    db.commit()
    return {'status': 'ok'}