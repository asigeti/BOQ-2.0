import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Create tables and run migrations on startup (for MVP)
try:
    from sqlalchemy import text, inspect
    Base.metadata.create_all(bind=engine)
    # Add missing columns to existing tables (lightweight migration)
    inspector = inspect(engine)
    if "project_plan" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("project_plan")]
        if "project_id" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE project_plan ADD COLUMN project_id INTEGER REFERENCES project(id) ON DELETE CASCADE"))
                print("Added project_id column to project_plan table")
    # Make user_id nullable (no auth in MVP)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE project_plan ALTER COLUMN user_id DROP NOT NULL"))
        conn.execute(text("ALTER TABLE project ALTER COLUMN user_id DROP NOT NULL"))
    print("Ensured user_id columns are nullable")
except Exception as e:
    print(f"WARNING: Failed to create/migrate tables: {e}")

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
