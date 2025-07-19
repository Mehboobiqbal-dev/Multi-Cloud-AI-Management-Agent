from cryptography.fernet import Fernet
import os

FERNET_KEY = os.environ.get('FERNET_KEY')
if not FERNET_KEY:
    # For production, set this in your environment and keep it secret!
    FERNET_KEY = Fernet.generate_key().decode()
    print(f"[WARNING] No FERNET_KEY set, using generated key: {FERNET_KEY}")
fernet = Fernet(FERNET_KEY.encode())

def encrypt(text: str) -> str:
    if not text:
        return ''
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    if not token:
        return ''
    return fernet.decrypt(token.encode()).decode()