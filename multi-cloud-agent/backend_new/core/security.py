from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import json
import base64
import os
import logging

from core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Fernet for encryption
try:
    fernet = Fernet(settings.FERNET_KEY.encode() if isinstance(settings.FERNET_KEY, str) else settings.FERNET_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Fernet: {e}")
    # Generate a new key if there's an issue
    key = Fernet.generate_key()
    fernet = Fernet(key)
    settings.FERNET_KEY = key.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SESSION_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def encrypt(data: Union[str, bytes, Dict, Any]) -> str:
    """
    Encrypt data using Fernet symmetric encryption.
    Handles string, bytes, or JSON-serializable objects.
    """
    try:
        if isinstance(data, dict) or not isinstance(data, (str, bytes)):
            data = json.dumps(data)
        
        if isinstance(data, str):
            data = data.encode()
            
        encrypted = fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise ValueError(f"Failed to encrypt data: {e}")

def decrypt(encrypted_data: str) -> Any:
    """
    Decrypt data that was encrypted with the encrypt function.
    Attempts to parse JSON if the decrypted result is valid JSON.
    """
    try:
        decoded = base64.urlsafe_b64decode(encrypted_data)
        decrypted = fernet.decrypt(decoded)
        result = decrypted.decode()
        
        # Try to parse as JSON if possible
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise ValueError(f"Failed to decrypt data: {e}")

def sandbox_execute(code: str, allowed_globals: Optional[Dict[str, Any]] = None) -> str:
    """
    Execute code in a restricted sandbox environment.
    
    This is a placeholder implementation. In a production environment,
    you would want to use a more secure sandboxing solution like:
    - RestrictedPython
    - PyPy sandbox
    - Docker containers
    - Separate process with resource limits
    """
    if allowed_globals is None:
        allowed_globals = {"__builtins__": {}}
    
    try:
        # This is NOT secure for production use
        result = {}
        exec(code, allowed_globals, result)
        return str(result)
    except Exception as e:
        return f"Sandbox execution error: {e}"