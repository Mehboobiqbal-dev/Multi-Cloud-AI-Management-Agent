from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "Multi-Cloud AI Management Agent"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    
    # Server settings
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", 8000))
    RELOAD: bool = os.environ.get("RELOAD", "True").lower() == "true"
    WORKERS: int = int(os.environ.get("WORKERS", 1))
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./database.db")
    
    # Security settings
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    FERNET_KEY: Optional[str] = os.environ.get("FERNET_KEY", "")
    FORCE_HTTPS: bool = os.environ.get("FORCE_HTTPS", "false").lower() == "true"
    
    # Authentication settings
    GOOGLE_CLIENT_ID: Optional[str] = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    
    # LLM settings
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "groq")  # groq, ollama, openai
    LLM_API_KEY: Optional[str] = os.environ.get("LLM_API_KEY", "")
    LLM_MODEL_NAME: str = os.environ.get("LLM_MODEL_NAME", "llama3-8b-8192")
    
    # Gemini settings (for backward compatibility)
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-pro")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", 60))
    
    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create settings instance
settings = Settings()

# Generate Fernet key if not provided
if not settings.FERNET_KEY:
    from cryptography.fernet import Fernet
    settings.FERNET_KEY = Fernet.generate_key().decode()

# Validate required settings in production
if settings.ENVIRONMENT == "production":
    required_vars = [
        ("DATABASE_URL", settings.DATABASE_URL),
        ("SESSION_SECRET", settings.SESSION_SECRET),
        ("LLM_API_KEY", settings.LLM_API_KEY),
    ]
    
    for var_name, var_value in required_vars:
        if not var_value:
            raise ValueError(f"Missing required environment variable in production: {var_name}")