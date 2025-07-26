from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SESSION_SECRET: str = "a-very-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    FORCE_HTTPS: bool = False
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-pro"

    class Config:
        env_file = "../.env"

settings = Settings()
