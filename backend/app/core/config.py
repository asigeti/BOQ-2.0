from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ConstructionAI Pro"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # AI
    OPENAI_API_KEY: str = ""
    
    # Database - Docker exposes PostgreSQL on localhost:7432
    DATABASE_URL: str = "postgresql://boq_user:boq_password@localhost:7432/boq_db"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:7001", "http://localhost:7000", "https://asigeti.github.io"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
