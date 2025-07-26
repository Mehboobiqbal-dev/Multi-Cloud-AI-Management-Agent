from cryptography.fernet import Fernet
import os

FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY environment variable must be set for production security.")
fernet = Fernet(FERNET_KEY.encode())

def encrypt(text: str) -> str:
    if not text:
        return ''
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    if not token:
        return ''
    return fernet.decrypt(token.encode()).decode()
