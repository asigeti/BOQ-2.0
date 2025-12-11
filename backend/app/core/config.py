from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "ConstructionAI Pro"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Provider: "openai" or "ollama"
    AI_PROVIDER: str = "openai"

    # OpenAI Settings
    OPENAI_API_KEY: str = ""

    # Gemini Settings (PRIMARY for PDF extraction)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-pro-preview"  # Latest Gemini 3 Pro (Nov 2025) - best multimodal

    # Anthropic Settings (FALLBACK for PDF extraction)
    ANTHROPIC_API_KEY: str = ""

    # Ollama Settings (Multi-Model Pipeline)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_HEBREW_MODEL: str = "aya-expanse:32b-q4_K_M"  # Hebrew specialist
    OLLAMA_REASONING_MODEL: str = "qwen2.5:72b-instruct-q4_K_M"  # 128k context
    OLLAMA_TIMEOUT: int = 600  # 10 minutes for large models
    OLLAMA_USE_MULTI_MODEL: bool = True  # Use Aya+Qwen pipeline

    @field_validator('OLLAMA_BASE_URL')
    @classmethod
    def validate_ollama_url(cls, v: str) -> str:
        # Ensure Ollama URL doesn't have /v1 suffix (that's for OpenAI compat)
        if v.endswith('/v1'):
            return v[:-3]
        return v

    # Database - Docker exposes PostgreSQL on localhost:7432
    DATABASE_URL: str = "postgresql://boq_user:boq_password@localhost:7432/boq_db"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:7001", "http://localhost:7000", "http://localhost:7777"]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
