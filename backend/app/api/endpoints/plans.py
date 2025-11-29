import shutil
import os
import uuid
from typing import List, Any
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.api import deps

router = APIRouter()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {'.pdf', '.dwg', '.dxf', '.ifc', '.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def validate_file_type(filename: str) -> tuple[bool, str]:
    """Validate file has an allowed extension"""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    return True, ext


def generate_safe_filename(original_filename: str) -> str:
    """Generate a safe filename using UUID while preserving extension"""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"


@router.post("/upload", response_model=schemas.Plan)
def upload_plan(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Upload a construction plan file and start processing.
    No authentication required for MVP.
    """
    # Validate file type
    is_valid, result = validate_file_type(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=result)
    file_ext = result

    # Create upload directory if needed
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Generate safe filename to prevent path traversal
    safe_filename = generate_safe_filename(file.filename)
    file_location = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Determine file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Use default user_id = 1 (no auth required)
    plan = models.ProjectPlan(
        filename=file.filename,
        file_path=file_location,
        file_type=file_ext,
        user_id=1,
        processing_status="pending",
        processing_progress=0
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Trigger background processing
    background_tasks.add_task(services.process_plan, plan.id, db)

    return plan

@router.get("/", response_model=List[schemas.Plan])
def read_plans(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all plans (no auth required).
    """
    plans = db.query(models.ProjectPlan).offset(skip).limit(limit).all()
    return plans

@router.get("/{plan_id}/quantities", response_model=List[schemas.MaterialQuantityOut])
def read_plan_quantities(
    plan_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Retrieve extracted quantities for a specific plan (no auth required).
    """
    plan = db.query(models.ProjectPlan).filter(models.ProjectPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return plan.materials

@router.get("/{plan_id}/status")
def get_plan_status(
    plan_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get processing status and progress for a plan (no auth required).
    """
    plan = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.id == plan_id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {
        "status": plan.processing_status,
        "progress": plan.processing_progress
    }
