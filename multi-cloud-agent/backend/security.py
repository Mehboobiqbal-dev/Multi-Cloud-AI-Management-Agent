from cryptography.fernet import Fernet
from core.config import settings

FERNET_KEY = settings.FERNET_KEY
if not FERNET_KEY:
    # In case the key is not in settings, generate a temporary one for development.
    # This should not happen if the .env file is set up correctly.
    print("Warning: FERNET_KEY not found in settings. Using a temporary key.")
    FERNET_KEY = Fernet.generate_key().decode()

fernet = Fernet(FERNET_KEY.encode())

def encrypt_text(text: str) -> str:
    """Encrypts a string."""
    if not text:
        return ''
    return fernet.encrypt(text.encode()).decode()

def decrypt_text(token: str) -> str:
    """Decrypts a token."""
    if not token:
        return ''
    return fernet.decrypt(token.encode()).decode()

def sandbox_execute(code: str) -> str:
    """Executes code in a sandboxed environment (placeholder)."""
    # Placeholder for sandboxing, e.g., using restricted Python or external service
    try:
        exec(code, {"__builtins__": {}})
        return "Code executed in sandbox."
    except Exception as e:
        return f"Sandbox execution error: {e}"