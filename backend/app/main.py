from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Create tables on startup (for MVP)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS - Allow frontend on port 7001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7001", "http://localhost:7000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to ConstructionAI Pro API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
