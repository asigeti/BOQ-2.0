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


@router.get("/plan-types")
def get_plan_types() -> Any:
    """
    Get list of supported plan types for PDF extraction.
    Returns plan types with Hebrew and English labels.
    """
    return services.get_supported_plan_types()


@router.post("/upload", response_model=schemas.Plan)
def upload_plan(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    plan_type: str = "general",  # For PDF: architectural, electrical, plumbing, etc.
) -> Any:
    """
    Upload a construction plan file and start processing.
    No authentication required for MVP.

    For PDF files, you can specify plan_type:
    - architectural: תכנית אדריכלית / בנייה
    - electrical: תכנית חשמל
    - plumbing: תכנית אינסטלציה
    - structural: תכנית קונסטרוקציה
    - hvac: תכנית מיזוג אוויר
    - windows_doors: לוח חלונות ודלתות
    - finishing: תכנית גמרים
    - landscape: תכנית גינון
    - general: תכנית כללית (default)
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

    # Trigger background processing with plan_type (used for PDF extraction)
    background_tasks.add_task(services.process_plan, plan.id, db, plan_type)

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


@router.get("/{plan_id}/boq")
def get_plan_boq(
    plan_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get Israeli BOQ (כתב כמויות) for a plan.

    NO FALLBACKS - Returns real GPT-4 + Dekel pricing data only.
    Throws error if real BOQ data is not available.
    """
    import json

    plan = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan.processing_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Plan processing not complete. Status: {plan.processing_status}"
        )

    # Check for real BOQ data (generated by GPT-4 + Dekel pricing)
    if not plan.boq_data:
        raise HTTPException(
            status_code=400,
            detail="No BOQ data available for this plan. "
                   "The plan was processed without GPT-4 pricing. "
                   "Re-upload and process the file to generate real BOQ with Dekel pricing."
        )

    # Return the real BOQ data
    try:
        boq = json.loads(plan.boq_data)
        return boq
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse BOQ data: {e}"
        )


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Delete a plan and its associated files and data.
    Cascade deletes all related materials.
    """
    plan = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # NEVER delete original user files - only delete uploaded copies
    # Files from user's project folders must NEVER be deleted
    # Only files we uploaded to our "uploads" folder can be deleted
    if plan.file_path and os.path.exists(plan.file_path):
        # Normalize paths for Windows (case-insensitive) comparison
        uploads_path = os.path.normcase(os.path.normpath(os.path.abspath(UPLOAD_DIR)))
        file_path_abs = os.path.normcase(os.path.normpath(os.path.abspath(plan.file_path)))

        # Extra safety: check that uploads_path is in our backend folder
        backend_dir = os.path.normcase(os.path.normpath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

        # Only delete if:
        # 1. File is inside our uploads folder (normalized comparison)
        # 2. Uploads folder is inside our backend directory (safety check)
        is_in_uploads = file_path_abs.startswith(uploads_path + os.sep) or file_path_abs == uploads_path
        is_safe_uploads = uploads_path.startswith(backend_dir)

        if is_in_uploads and is_safe_uploads:
            try:
                os.remove(plan.file_path)
            except Exception as e:
                # Log but don't fail - DB cleanup is more important
                pass
        # Otherwise: file is a user's original file - DO NOT delete it
        # This includes files from scanned project folders

    # Delete from database (cascade will delete materials)
    db.delete(plan)
    db.commit()

    return {"message": "Plan deleted successfully", "id": plan_id}
