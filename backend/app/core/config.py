import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NexaGrid Real-Time Code Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "nexagrid-faang-secret-key-super-secure-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/nexagrid")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AI Service
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    AI_MODEL: str = "claude-haiku-4-5-20251001"
    
    # Sandbox Execution
    MAX_MEMORY_MB: int = 128
    EXECUTION_TIMEOUT_SECONDS: int = 10
    MAX_OUTPUT_BYTES: int = 64 * 1024
    
    class Config:
        case_sensitive = True

settings = Settings()
