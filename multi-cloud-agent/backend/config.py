from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SESSION_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    FORCE_HTTPS: bool = False
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-pro"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# Enforce required secrets
for var_name, var_value in [
    ("DATABASE_URL", settings.DATABASE_URL),
    ("SESSION_SECRET", settings.SESSION_SECRET),
    ("GOOGLE_CLIENT_ID", settings.GOOGLE_CLIENT_ID),
    ("GOOGLE_CLIENT_SECRET", settings.GOOGLE_CLIENT_SECRET),
    ("GEMINI_API_KEY", settings.GEMINI_API_KEY)
]:
    if not var_value:
        raise RuntimeError(f"A required environment variable is missing: {var_name}")
