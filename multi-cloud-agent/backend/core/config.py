from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Load environment variables from both project root and backend/.env
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
# Load root .env first, then backend/.env to allow backend overrides without clobbering root
load_dotenv(os.path.join(_project_root, ".env"))
load_dotenv(os.path.join(_project_root, "backend", ".env"))

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
    ALLOWED_ORIGINS: str = os.environ.get("ALLOWED_ORIGINS", "*")
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{_project_root}/backend/database.db")
    
    # Security settings
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    FERNET_KEY: Optional[str] = os.environ.get("FERNET_KEY", "")
    FORCE_HTTPS: bool = os.environ.get("FORCE_HTTPS", "false").lower() == "true"
    
    # Authentication settings
    GOOGLE_CLIENT_ID: Optional[str] = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    
    # Legacy LLM settings (deprecated - use Gemini instead)
    # These are kept for backward compatibility but not used
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "gemini")
    LLM_API_KEY: Optional[str] = os.environ.get("LLM_API_KEY", "")
    LLM_MODEL_NAME: str = os.environ.get("LLM_MODEL_NAME", "deprecated")
    
    # Gemini settings (for backward compatibility)
    GEMINI_API_KEYS: str = os.environ.get("GEMINI_API_KEYS", "")
    GEMINI_API_KEYS_LIST: List[str] = [k.strip() for k in GEMINI_API_KEYS.split(",") if k.strip()]
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-pro")
    
    # Auto content generation settings
    ENABLE_AUTO_CONTENT: bool = os.environ.get("ENABLE_AUTO_CONTENT", "True").lower() == "true"
    AUTO_CONTENT_INTERVAL_MINUTES: int = int(os.environ.get("AUTO_CONTENT_INTERVAL_MINUTES", 360))
    AUTO_CONTENT_TOPICS: str = os.environ.get("AUTO_CONTENT_TOPICS", "python,data structures,algorithms,system design,cloud computing,devops,ai ml")
    AUTO_CONTENT_GENERATE_EXAMS: bool = os.environ.get("AUTO_CONTENT_GENERATE_EXAMS", "True").lower() == "true"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("RATE_LIMIT_PER_MINUTE", 60))
    
    # Logging
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Resilience and retry settings
    MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", 3))
    INITIAL_RETRY_DELAY: float = float(os.environ.get("INITIAL_RETRY_DELAY", 2.0))
    MAX_RETRY_DELAY: float = float(os.environ.get("MAX_RETRY_DELAY", 60.0))
    NETWORK_TIMEOUT: int = int(os.environ.get("NETWORK_TIMEOUT", 30))
    
    # Circuit breaker settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(os.environ.get("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(os.environ.get("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", 60))
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: bool = os.environ.get("CIRCUIT_BREAKER_EXPECTED_EXCEPTION", "True").lower() == "true"
    
    # Memory and embedding settings
    EMBEDDING_BATCH_SIZE: int = int(os.environ.get("EMBEDDING_BATCH_SIZE", 10))
    MEMORY_CACHE_SIZE: int = int(os.environ.get("MEMORY_CACHE_SIZE", 1000))
    ENABLE_LOCAL_EMBEDDINGS: bool = os.environ.get("ENABLE_LOCAL_EMBEDDINGS", "False").lower() == "true"
    LOCAL_EMBEDDING_MODEL: str = os.environ.get("LOCAL_EMBEDDING_MODEL", "sentence-transformers/paraphrase-MiniLM-L3-v2")
    HIGH_MEMORY_MODE: bool = os.environ.get("HIGH_MEMORY_MODE", "False").lower() == "true"
    
    # Self-learning settings
    ENABLE_SELF_LEARNING: bool = os.environ.get("ENABLE_SELF_LEARNING", "True").lower() == "true"
    LEARNING_CONFIDENCE_THRESHOLD: float = float(os.environ.get("LEARNING_CONFIDENCE_THRESHOLD", 0.75))
    AUTO_APPLY_FIXES: bool = os.environ.get("AUTO_APPLY_FIXES", "False").lower() == "true"
    
    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = os.environ.get("ENABLE_PERFORMANCE_MONITORING", "True").lower() == "true"
    SLOW_OPERATION_THRESHOLD: float = float(os.environ.get("SLOW_OPERATION_THRESHOLD", 5.0))
    PERFORMANCE_MONITORING_SAMPLE_RATE: float = float(os.environ.get("PERFORMANCE_MONITORING_SAMPLE_RATE", 0.1))
    
    # Agent execution resilience
    MAX_CONSECUTIVE_FAILURES: int = int(os.environ.get("MAX_CONSECUTIVE_FAILURES", 3))
    AGENT_DECISION_RETRY_ATTEMPTS: int = int(os.environ.get("AGENT_DECISION_RETRY_ATTEMPTS", 3))
    BROWSER_ERROR_EXTRA_DELAY: bool = os.environ.get("BROWSER_ERROR_EXTRA_DELAY", "True").lower() == "true"
    
    # Form automation resilience
    FORM_ELEMENT_WAIT_STRATEGIES: int = int(os.environ.get("FORM_ELEMENT_WAIT_STRATEGIES", 3))
    FORM_ALTERNATIVE_SELECTORS: bool = os.environ.get("FORM_ALTERNATIVE_SELECTORS", "True").lower() == "true"
    FORM_PARTIAL_SUCCESS_ALLOWED: bool = os.environ.get("FORM_PARTIAL_SUCCESS_ALLOWED", "True").lower() == "true"
    
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
    ]
    
    # Gemini API keys are optional
    for var_name, var_value in required_vars:
        if not var_value or var_value == "your-secret-key-change-in-production":
            raise ValueError(f"Missing or default value for required environment variable in production: {var_name}")
    
    # Disable reload in production
    settings.RELOAD = False
    settings.DEBUG = False
