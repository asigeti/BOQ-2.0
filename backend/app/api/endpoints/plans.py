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


@router.get("/{plan_id}/boq")
def get_plan_boq(
    plan_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get Israeli BOQ (כתב כמויות) for a plan.
    Converts extracted materials into proper BOQ format with chapters.
    """
    from datetime import datetime

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

    # Get materials from database
    materials = plan.materials

    # Group materials by type into chapters
    chapters_map = {
        "01": {"name_he": "עבודות עפר", "name_en": "Earthworks", "items": []},
        "02": {"name_he": "בטון", "name_en": "Concrete", "items": []},
        "03": {"name_he": "בניה", "name_en": "Masonry", "items": []},
        "04": {"name_he": "איטום", "name_en": "Waterproofing", "items": []},
        "05": {"name_he": "טיח", "name_en": "Plastering", "items": []},
        "06": {"name_he": "ריצוף וחיפוי", "name_en": "Flooring & Tiling", "items": []},
        "07": {"name_he": "אלומיניום וזכוכית", "name_en": "Aluminum & Glass", "items": []},
        "08": {"name_he": "נגרות", "name_en": "Carpentry", "items": []},
        "09": {"name_he": "צבע", "name_en": "Painting", "items": []},
        "10": {"name_he": "אינסטלציה", "name_en": "Plumbing", "items": []},
        "11": {"name_he": "חשמל", "name_en": "Electrical", "items": []},
        "12": {"name_he": "מיזוג אוויר", "name_en": "HVAC", "items": []},
        "99": {"name_he": "שונות", "name_en": "Miscellaneous", "items": []},
    }

    # Classify materials into chapters
    for i, mat in enumerate(materials):
        mat_name = mat.material_name.lower()

        # Simple classification based on keywords
        if any(k in mat_name for k in ["door", "דלת", "window", "חלון", "frame"]):
            chapter = "08"
        elif any(k in mat_name for k in ["concrete", "בטון", "foundation"]):
            chapter = "02"
        elif any(k in mat_name for k in ["block", "בלוק", "wall", "קיר", "brick"]):
            chapter = "03"
        elif any(k in mat_name for k in ["floor", "ריצוף", "tile", "אריח"]):
            chapter = "06"
        elif any(k in mat_name for k in ["paint", "צבע"]):
            chapter = "09"
        elif any(k in mat_name for k in ["pipe", "צינור", "plumb", "אינסטלציה"]):
            chapter = "10"
        elif any(k in mat_name for k in ["electric", "חשמל", "wire", "כבל"]):
            chapter = "11"
        elif any(k in mat_name for k in ["ac", "מזגן", "hvac", "מיזוג"]):
            chapter = "12"
        elif any(k in mat_name for k in ["aluminum", "אלומיניום", "glass", "זכוכית"]):
            chapter = "07"
        else:
            chapter = "99"

        # Estimate price (placeholder - would use Dekel pricing in production)
        unit_price = 100.0  # Default placeholder
        quantity = mat.quantity or 1.0
        total_price = unit_price * quantity

        item = {
            "item_code": f"{chapter}.{str(i + 1).zfill(2)}",
            "dekel_code": None,
            "description_he": mat.material_name,
            "description_en": mat.material_name,
            "quantity": quantity,
            "unit": mat.unit or "יח'",
            "unit_price": unit_price,
            "total_price": total_price,
            "confidence": mat.confidence_score or 0.5,
            "notes": None,
        }
        chapters_map[chapter]["items"].append(item)

    # Build chapters list (only non-empty chapters)
    chapters = []
    subtotal = 0.0

    for code, ch_data in chapters_map.items():
        if ch_data["items"]:
            chapter_total = sum(item["total_price"] for item in ch_data["items"])
            subtotal += chapter_total

            chapters.append({
                "chapter_code": code,
                "chapter_name_he": ch_data["name_he"],
                "chapter_name_en": ch_data["name_en"],
                "items": ch_data["items"],
                "chapter_total": chapter_total,
            })

    # Calculate VAT
    vat_rate = 0.17
    vat_amount = subtotal * vat_rate
    grand_total = subtotal + vat_amount

    return {
        "project_name": plan.filename.rsplit(".", 1)[0],
        "filename": plan.filename,
        "date": datetime.now().isoformat(),
        "chapters": chapters,
        "summary": {
            "subtotal": subtotal,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "grand_total": grand_total,
        },
        "notes": [],
        "metadata": {
            "extraction_method": "auto",
            "processing_time_seconds": 0,
            "generated_at": datetime.now().isoformat(),
        }
    }
