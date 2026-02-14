import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Create tables on startup (for MVP)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"WARNING: Failed to create tables: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler so errors return JSON with CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to ConstructionAI Pro API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/debug/db")
async def debug_db():
    """Check database connection and tables."""
    from app.db.session import SessionLocal
    from sqlalchemy import text
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result]
        db.close()
        return {"status": "connected", "tables": tables}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e), "type": type(e).__name__},
        )
