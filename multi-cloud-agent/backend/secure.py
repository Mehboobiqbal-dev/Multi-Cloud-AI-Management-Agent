from cryptography.fernet import Fernet
from config import settings

FERNET_KEY = settings.FERNET_KEY
if not FERNET_KEY:
    # In case the key is not in settings, generate a temporary one for development.
    # This should not happen if the .env file is set up correctly.
    print("Warning: FERNET_KEY not found in settings. Using a temporary key.")
    FERNET_KEY = Fernet.generate_key().decode()

fernet = Fernet(FERNET_KEY.encode())

def encrypt(text: str) -> str:
    if not text:
        return ''
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    if not token:
        return ''
    return fernet.decrypt(token.encode()).decode()
