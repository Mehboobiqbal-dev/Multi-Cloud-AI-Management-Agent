from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./database.db")
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    FORCE_HTTPS: bool = os.environ.get("FORCE_HTTPS", "false").lower() == "true"
    # Gemini settings are managed in core/config.py
    FERNET_KEY: str = os.environ.get("FERNET_KEY", "")
    LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
    LLM_MODEL_NAME: str = os.environ.get("LLM_MODEL_NAME", "")
    PORT: int = int(os.environ.get("PORT", 8000))
    HOST: str = os.environ.get("HOST", "0.0.0.0")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

if not settings.DATABASE_URL:
    settings.DATABASE_URL = "sqlite:///./database.db"
if not settings.FERNET_KEY:
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

# Only enforce required secrets in production
if os.environ.get("ENVIRONMENT", "development") == "production":
    for var_name, var_value in [
        ("DATABASE_URL", settings.DATABASE_URL),
        ("SESSION_SECRET", settings.SESSION_SECRET),
        ("GOOGLE_CLIENT_ID", settings.GOOGLE_CLIENT_ID),
        ("GOOGLE_CLIENT_SECRET", settings.GOOGLE_CLIENT_SECRET),
        # ("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    ]:
        if not var_value:
            raise RuntimeError(f"A required environment variable is missing: {var_name}")
