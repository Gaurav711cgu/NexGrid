from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "NexaGrid Real-Time Code Platform"
    VERSION: str = "1.2.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"

    # Auth — no fallback, raises ValidationError at startup if missing
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NexGrid"
    NEXAGRID_ENV: str = "development"
    
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # CORS — set CORS_ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/nexagrid"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Service
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "claude-haiku-4-5-20251001"
    AI_PROMPT_VERSION: str = "v1"

    # Sandbox Execution
    MAX_MEMORY_MB: int = 128
    EXECUTION_TIMEOUT_SECONDS: int = 10
    MAX_OUTPUT_BYTES: int = 64 * 1024

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v


settings = Settings()
