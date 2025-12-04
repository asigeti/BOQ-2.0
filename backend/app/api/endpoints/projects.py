import os
import io
import json
import shutil
from pathlib import Path
from typing import List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd

from app import models, schemas, services
from app.api import deps

router = APIRouter()


def scan_folder_for_dwg(folder_path: str) -> List[str]:
    """
    Recursively scan a folder for DWG files.
    Returns list of absolute paths to DWG files.
    """
    dwg_files = []
    folder = Path(folder_path)

    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")

    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")

    # Recursively find all .dwg files
    for dwg_file in folder.rglob("*.dwg"):
        dwg_files.append(str(dwg_file.absolute()))

    # Also check for .dxf files
    for dxf_file in folder.rglob("*.dxf"):
        dwg_files.append(str(dxf_file.absolute()))

    return sorted(dwg_files)


def process_project_files(project_id: int, db: Session):
    """
    Background task to EXTRACT data from all DWG files in a project.

    NEW FLOW: This only extracts data, does NOT generate BOQ.
    After extraction completes, user reviews layers and confirms selection.
    Then BOQ generation starts separately.
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.error(f"Project {project_id} not found")
        return

    try:
        logger.info(f"Starting EXTRACTION for project {project_id}")
        project.processing_status = "processing"
        db.commit()

        plans = project.plans
        total = len(plans)
        processed = 0

        for plan in plans:
            try:
                logger.info(f"Extracting plan {plan.id}: {plan.filename}")
                # Extract data only (no BOQ generation)
                services.process_plan(plan.id, db)
                processed += 1
                project.processed_files = processed
                project.processing_progress = int((processed / total) * 100)
                db.commit()
                logger.info(f"Plan {plan.id} extraction completed")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Plan {plan.id} failed: {error_msg}")
                logger.error(traceback.format_exc())
                plan.processing_status = "failed"
                db.commit()

        # Set status to "extracted" - waiting for user to review and confirm layers
        project.processing_status = "extracted"
        project.processing_progress = 100
        db.commit()
        logger.info(f"Project {project_id} extraction completed - waiting for user review")

    except Exception as e:
        logger.error(f"Project {project_id} extraction failed: {e}")
        logger.error(traceback.format_exc())
        project.processing_status = "failed"
        db.commit()


@router.post("/", response_model=schemas.Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectCreate,
) -> Any:
    """
    Create a new project.
    """
    project = models.Project(
        name=project_in.name,
        description=project_in.description,
        folder_path=project_in.folder_path,
        user_id=1,  # Default user for MVP
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=List[schemas.Project])
def list_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all projects.
    """
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return projects


@router.get("/browse-folder")
def browse_folder(
    path: str = "",
) -> Any:
    """
    Browse folders on the local filesystem.
    Returns list of subfolders for navigation.
    """
    import string

    # If no path provided, return available drives (Windows)
    if not path or path == "":
        drives = []
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.append({
                    "name": f"{letter}:",
                    "path": drive_path,
                    "type": "drive",
                })
        return {"current_path": "", "parent_path": None, "folders": drives}

    folder = Path(path)

    if not folder.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")

    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    # Get parent path
    parent_path = str(folder.parent) if folder.parent != folder else None

    # Get subfolders
    subfolders = []
    try:
        for item in sorted(folder.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                try:
                    # Check if accessible
                    list(item.iterdir())
                    subfolders.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "folder",
                    })
                except PermissionError:
                    # Skip folders we can't access
                    pass
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "current_path": str(folder),
        "parent_path": parent_path,
        "folders": subfolders,
    }


@router.post("/scan-folder", response_model=schemas.FolderScanResult)
def scan_folder(
    *,
    scan_request: schemas.ProjectScanRequest,
) -> Any:
    """
    Scan a folder for DWG files (preview before creating project).
    """
    try:
        dwg_files = scan_folder_for_dwg(scan_request.folder_path)
        return {
            "folder_path": scan_request.folder_path,
            "dwg_files": dwg_files,
            "total_count": len(dwg_files),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=schemas.ProjectWithPlans)
def get_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific project with its plans.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    *,
    db: Session = Depends(deps.get_db),
    project_in: schemas.ProjectUpdate,
) -> Any:
    """
    Update a project.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.folder_path is not None:
        project.folder_path = project_in.folder_path

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Delete a project and all its plans, materials, and associated files.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete physical files for all plans
    deleted_files = 0
    for plan in project.plans:
        if plan.file_path and os.path.exists(plan.file_path):
            try:
                os.remove(plan.file_path)
                deleted_files += 1
            except Exception:
                pass  # Log but don't fail - DB cleanup is more important

    # Delete from database (cascade will delete plans and materials)
    plan_count = len(project.plans)
    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully",
        "id": project_id,
        "deleted_plans": plan_count,
        "deleted_files": deleted_files
    }


@router.post("/{project_id}/scan", response_model=schemas.ProjectWithPlans)
def scan_project_folder(
    project_id: int,
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Scan project folder for DWG files and create plans for each.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.folder_path:
        raise HTTPException(status_code=400, detail="Project has no folder path set")

    try:
        project.processing_status = "scanning"
        db.commit()

        # Scan for DWG files
        dwg_files = scan_folder_for_dwg(project.folder_path)

        # Create a plan for each DWG file
        for file_path in dwg_files:
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()

            # Check if plan already exists for this file
            existing = db.query(models.ProjectPlan).filter(
                models.ProjectPlan.project_id == project_id,
                models.ProjectPlan.file_path == file_path
            ).first()

            if not existing:
                plan = models.ProjectPlan(
                    filename=filename,
                    file_path=file_path,
                    file_type=file_ext,
                    user_id=1,
                    project_id=project_id,
                    processing_status="pending",
                    processing_progress=0,
                )
                db.add(plan)

        project.total_files = len(dwg_files)
        project.processing_status = "pending"
        db.commit()
        db.refresh(project)

        return project

    except ValueError as e:
        project.processing_status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/process")
def process_project(
    project_id: int,
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Start processing all DWG files in the project.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.plans:
        raise HTTPException(status_code=400, detail="Project has no files to process")

    # Start background processing
    background_tasks.add_task(process_project_files, project_id, db)

    return {"message": "Processing started", "total_files": len(project.plans)}


@router.get("/{project_id}/status")
def get_project_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get processing status for a project.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "status": project.processing_status,
        "progress": project.processing_progress,
        "total_files": project.total_files,
        "processed_files": project.processed_files,
    }


@router.get("/{project_id}/boq")
def get_project_boq(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get aggregated Israeli BOQ for all files in the project from database.
    Returns BOQ data with source tracking (file name + layer name).
    """
    from app.models.boq_item import BOQItem

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all non-deleted BOQ items from database
    items = db.query(BOQItem).filter(
        BOQItem.project_id == project_id,
        BOQItem.is_deleted == False
    ).order_by(BOQItem.chapter_code, BOQItem.item_code).all()

    if not items:
        raise HTTPException(
            status_code=400,
            detail="No BOQ data available. Process files first to generate BOQ."
        )

    # Group items by chapter
    chapters = {}
    for item in items:
        if item.chapter_code not in chapters:
            chapters[item.chapter_code] = {
                "chapter_code": item.chapter_code,
                "chapter_name_he": item.chapter_name_he,
                "chapter_name_en": item.chapter_name_en,
                "items": [],
                "chapter_total": 0
            }

        chapters[item.chapter_code]["items"].append({
            "id": item.id,  # Include ID for editing
            "item_code": item.item_code,
            "description_he": item.description_he,
            "description_en": item.description_en,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "source_filename": item.source_filename,  # NEW - source tracking
            "source_layer": item.source_layer,  # NEW - source tracking
            "confidence": item.confidence,
            "user_notes": item.user_notes,  # NEW - user notes
            "is_modified": item.is_modified  # NEW - modification flag
        })
        chapters[item.chapter_code]["chapter_total"] += item.total_price

    # Calculate totals
    subtotal = sum(ch["chapter_total"] for ch in chapters.values())
    vat_amount = subtotal * 0.17
    grand_total = subtotal + vat_amount

    # Get source files
    source_files = list(set(item.source_filename for item in items if item.source_filename))

    return {
        "project_name": project.name,
        "project_id": project.id,
        "date": datetime.now().isoformat(),
        "chapters": list(chapters.values()),
        "summary": {
            "subtotal": round(subtotal, 2),
            "vat_rate": 0.17,
            "vat_amount": round(vat_amount, 2),
            "grand_total": round(grand_total, 2),
            "total_files": len(project.plans),
            "total_items": len(items)
        },
        "source_files": source_files,
        "notes": []
    }


def _aggregate_real_boq_data(project, plans_with_boq) -> dict:
    """Aggregate REAL BOQ data from GPT-4 + Dekel pricing"""
    import json

    # Aggregate chapters from all plans
    chapters_map = {}

    for plan in plans_with_boq:
        boq_data = json.loads(plan.boq_data)

        for chapter in boq_data.get("chapters", []):
            ch_code = chapter.get("chapter_code", "99")

            if ch_code not in chapters_map:
                chapters_map[ch_code] = {
                    "chapter_code": ch_code,
                    "chapter_name_he": chapter.get("chapter_name_he", "שונות"),
                    "chapter_name_en": chapter.get("chapter_name_en", "Miscellaneous"),
                    "items": [],
                    "chapter_total": 0.0,
                }

            # Add items from this plan
            for item in chapter.get("items", []):
                # Add source file info
                item["source_file"] = plan.filename
                chapters_map[ch_code]["items"].append(item)
                chapters_map[ch_code]["chapter_total"] += item.get("total_price", 0)

    # Build final chapters list sorted by code
    chapters = []
    subtotal = 0.0

    for ch_code in sorted(chapters_map.keys()):
        ch_data = chapters_map[ch_code]
        ch_data["chapter_total"] = round(ch_data["chapter_total"], 2)
        subtotal += ch_data["chapter_total"]
        chapters.append(ch_data)

    # Calculate VAT
    vat_rate = 0.17
    vat_amount = subtotal * vat_rate
    grand_total = subtotal + vat_amount

    return {
        "project_name": project.name,
        "project_id": project.id,
        "date": datetime.now().isoformat(),
        "chapters": chapters,
        "summary": {
            "subtotal": round(subtotal, 2),
            "vat_rate": vat_rate,
            "vat_amount": round(vat_amount, 2),
            "grand_total": round(grand_total, 2),
            "total_files": len(plans_with_boq),
            "total_items": sum(len(ch["items"]) for ch in chapters),
        },
        "source_files": [p.filename for p in plans_with_boq],
        "notes": [],
        "metadata": {
            "extraction_method": "gpt4_dekel_pricing",
            "generated_at": datetime.now().isoformat(),
            "pricing_source": "מחירון דקל",
        }
    }


@router.get("/{project_id}/extraction")
def get_project_extraction_data(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get AutoCAD extraction data summary for all files in the project.
    Shows what was extracted from each DWG file.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    extraction_results = []
    total_area_m2 = 0.0
    total_blocks = 0
    total_text = 0
    total_layers = 0
    total_polylines = 0

    for plan in project.plans:
        plan_extraction = {
            "plan_id": plan.id,
            "filename": plan.filename,
            "processing_status": plan.processing_status,
            "extraction_data": None,
        }

        if plan.extraction_data:
            try:
                data = json.loads(plan.extraction_data)
                plan_extraction["extraction_data"] = data

                # Aggregate totals
                total_blocks += data.get("blocks_count", 0)
                total_text += data.get("text_count", 0)
                total_layers += data.get("layers_count", 0)
                total_polylines += data.get("polylines_count", 0)

                # Convert area from cm² to m² (divide by 10000)
                area_cm2 = data.get("total_area_cm2", 0)
                area_m2 = area_cm2 / 10000.0
                plan_extraction["area_m2"] = round(area_m2, 2)
                total_area_m2 += area_m2
            except json.JSONDecodeError:
                pass

        extraction_results.append(plan_extraction)

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_files": len(project.plans),
        "extraction_summary": {
            "total_area_m2": round(total_area_m2, 2),
            "total_blocks": total_blocks,
            "total_text_entities": total_text,
            "total_layers": total_layers,
            "total_polylines": total_polylines,
        },
        "files": extraction_results,
    }


@router.get("/{project_id}/boq/export")
def export_project_boq_to_excel(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Export project BOQ to Excel file with source tracking.
    Creates a professional Israeli BOQ spreadsheet with all chapters.
    """
    from app.models.boq_item import BOQItem

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get BOQ data from database instead of JSON
    boq_data = get_project_boq(project_id, db)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            "פרט": [
                "שם פרויקט",
                "תאריך",
                "מספר קבצים",
                "סה\"כ פריטים",
                "סה\"כ לפני מע\"מ",
                "מע\"מ (17%)",
                "סה\"כ כולל מע\"מ"
            ],
            "ערך": [
                boq_data["project_name"],
                boq_data["date"][:10],
                boq_data["summary"]["total_files"],
                boq_data["summary"]["total_items"],
                f"₪{boq_data['summary']['subtotal']:,.2f}",
                f"₪{boq_data['summary']['vat_amount']:,.2f}",
                f"₪{boq_data['summary']['grand_total']:,.2f}"
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="סיכום", index=False)

        # Each chapter as a sheet
        for chapter in boq_data.get("chapters", []):
            if chapter.get("items"):
                items_data = []
                for item in chapter["items"]:
                    items_data.append({
                        "קוד": item.get("item_code", ""),
                        "קוד דקל": item.get("dekel_code", ""),
                        "תיאור": item.get("description_he", ""),
                        "Description": item.get("description_en", ""),
                        "כמות": item.get("quantity", 0),
                        "יחידה": item.get("unit", ""),
                        "מחיר יחידה": item.get("unit_price", 0),
                        "סה\"כ": item.get("total_price", 0),
                        "קובץ מקור": item.get("source_filename", "") or item.get("source_file", ""),  # NEW
                        "שכבה": item.get("source_layer", ""),  # NEW
                        "הערות משתמש": item.get("user_notes", "") or item.get("notes", "") or "",  # NEW
                        "ביטחון": f"{item.get('confidence', 0) * 100:.0f}%",
                    })

                sheet_name = f"{chapter['chapter_code']}-{chapter['chapter_name_he']}"[:31]
                pd.DataFrame(items_data).to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)

    # Return as downloadable file
    # Use ASCII-safe filename for Content-Disposition, with UTF-8 encoded filename* for modern browsers
    from urllib.parse import quote
    safe_name = f"BOQ_Project{project.id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    full_name = f"BOQ_{project.name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    encoded_name = quote(full_name, safe='')

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{encoded_name}"
        }
    )


@router.get("/{project_id}/boq/export/pdf")
def export_project_boq_to_pdf(
    project_id: int,
    logo_path: Optional[str] = None,
    company_name: Optional[str] = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Export project BOQ to professional PDF proposal.
    Creates construction-industry standard BOQ PDF with:
    - Professional cover page with optional company logo
    - Executive summary
    - Detailed BOQ tables by chapter
    - Terms and conditions
    - Page headers/footers
    """
    from app.services.pdf_generator import generate_boq_pdf

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get BOQ data from database
    boq_data = get_project_boq(project_id, db)

    # Check if logo path exists
    if logo_path:
        logo_full_path = Path(logo_path)
        if not logo_full_path.exists():
            logo_path = None

    # Generate PDF
    try:
        pdf_buffer = generate_boq_pdf(
            boq_data=boq_data,
            logo_path=logo_path,
            company_name=company_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )

    # Create filename
    from urllib.parse import quote
    safe_name = f"BOQ_Project{project.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    full_name = f"BOQ_{project.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    encoded_name = quote(full_name, safe='')

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{encoded_name}"
        }
    )


@router.get("/{project_id}/extraction-preview")
def get_extraction_preview(
    project_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get extraction data with SMART layer categorization for user review.

    NEW: Layers are grouped by purpose (building, site boundaries, infrastructure, etc.)
    with smart auto-detection based on names, areas, and patterns.

    Returns:
    - Grouped layers (building, structural, site_boundary, infrastructure, landscape, etc.)
    - Group metadata (names, icons, descriptions, default selections)
    - AI validation warnings (unrealistic areas, site boundaries included, etc.)

    User can then POST to /extraction-confirm with selected layers.
    """
    from app.services.layer_categorizer import (
        categorize_layer,
        get_group_metadata,
        validate_selection,
        LayerGroup,
    )

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Collect all layers for categorization
    all_layers = []
    files_preview = []

    for plan in project.plans:
        file_preview = {
            "plan_id": plan.id,
            "filename": plan.filename,
            "processing_status": plan.processing_status,
            "has_extraction": False,
            "layer_groups": {},
        }

        extraction_layers = plan.extraction_layers
        if extraction_layers:
            file_preview["has_extraction"] = True
            layer_groups = {}

            for layer in extraction_layers:
                # Smart categorization
                from_xref = "|" in layer.layer_name or layer.layer_name.startswith("xref")
                group, confidence = categorize_layer(
                    layer.layer_name,
                    layer.area_m2,
                    layer.polyline_count,
                    from_xref
                )

                layer_info = {
                    "id": layer.id,
                    "layer_name": layer.layer_name,
                    "area_m2": round(layer.area_m2, 2),
                    "polyline_count": layer.polyline_count,
                    "hatch_count": layer.hatch_count,
                    "group": group.value,
                    "confidence": round(confidence, 2),
                    "user_selected": layer.user_selected,
                }

                # Store for validation
                all_layers.append(layer_info)

                # Group layers
                if group.value not in layer_groups:
                    layer_groups[group.value] = {
                        "metadata": get_group_metadata(group),
                        "layers": [],
                        "total_area_m2": 0,
                    }

                layer_groups[group.value]["layers"].append(layer_info)
                layer_groups[group.value]["total_area_m2"] += layer.area_m2

            # Sort layers within each group by area
            for group_data in layer_groups.values():
                group_data["layers"].sort(key=lambda x: x["area_m2"], reverse=True)
                group_data["total_area_m2"] = round(group_data["total_area_m2"], 2)

            file_preview["layer_groups"] = layer_groups

        files_preview.append(file_preview)

    # Auto-select layers based on group defaults
    default_selected_ids = []
    default_selected_names = []
    for layer in all_layers:
        group = LayerGroup(layer["group"])
        metadata = get_group_metadata(group)
        if metadata.get("default_selected", False):
            default_selected_ids.append(layer["id"])
            default_selected_names.append(layer["layer_name"])

    # Validate default selection (using names for backwards compatibility)
    validation = validate_selection(all_layers, default_selected_names)

    # Calculate project-wide totals by group
    group_totals = {}
    for group in LayerGroup:
        group_totals[group.value] = {
            "metadata": get_group_metadata(group),
            "total_area_m2": 0,
            "layer_count": 0,
        }

    for layer in all_layers:
        group = layer["group"]
        group_totals[group]["total_area_m2"] += layer["area_m2"]
        group_totals[group]["layer_count"] += 1

    for group_data in group_totals.values():
        group_data["total_area_m2"] = round(group_data["total_area_m2"], 2)

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total_files": len(project.plans),
        "files_with_extraction": sum(1 for f in files_preview if f["has_extraction"]),
        "files": files_preview,
        "group_totals": group_totals,
        "default_selection": {
            "selected_layer_ids": default_selected_ids,
            "selected_layer_names": default_selected_names,
            "selected_area_m2": validation["building_area_m2"],
        },
        "validation": validation,
    }


def generate_project_boq_background(project_id: int, selected_layers: set, custom_area: float, db: Session):
    """
    Background task to generate BOQ for all plans in a project.
    Called after user confirms extraction layer selection.
    """
    import logging
    import traceback
    logger = logging.getLogger(__name__)

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.error(f"Project {project_id} not found")
        return

    try:
        logger.info(f"Starting BOQ generation for project {project_id}")
        project.processing_status = "generating_boq"
        db.commit()

        # Generate BOQ for each extracted plan
        for plan in project.plans:
            if plan.processing_status == "extracted" and plan.extraction_data:
                try:
                    logger.info(f"Generating BOQ for plan {plan.id}: {plan.filename}")
                    services.generate_boq_for_plan(
                        plan_id=plan.id,
                        db=db,
                        selected_layers=selected_layers,
                        custom_area_m2=custom_area
                    )
                    logger.info(f"BOQ generated for plan {plan.id}")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"BOQ generation failed for plan {plan.id}: {error_msg}")
                    logger.error(traceback.format_exc())
                    plan.processing_status = "failed"
                    db.commit()

        # Check if all plans completed
        all_completed = all(p.processing_status == "completed" for p in project.plans)
        if all_completed:
            project.processing_status = "completed"
        else:
            # At least some failed
            project.processing_status = "partial"

        db.commit()
        logger.info(f"BOQ generation completed for project {project_id}")

    except Exception as e:
        logger.error(f"Project {project_id} BOQ generation failed: {e}")
        logger.error(traceback.format_exc())
        project.processing_status = "failed"
        db.commit()


@router.post("/{project_id}/extraction-confirm")
def confirm_extraction_selection(
    project_id: int,
    *,
    db: Session = Depends(deps.get_db),
    selection: schemas.ExtractionSelectionRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Confirm layer selection and START BOQ generation.

    Request body:
    {
        "selected_layer_ids": [123, 456, 789],  // Layer IDs to include (unique across all files)
        "custom_area_m2": 500.0  // Optional: override with manual area
    }

    This will:
    1. Store the user's layer selection in DB
    2. Calculate the final area from selected layers
    3. START BOQ generation in background (AI + Dekel pricing)
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    selected_layer_ids = set(selection.selected_layer_ids) if selection.selected_layer_ids else set()
    custom_area = selection.custom_area_m2

    # Calculate selected area from layers and update DB
    selected_area_m2 = 0.0
    selected_layer_names = []

    for plan in project.plans:
        # Update extraction layers in DB with user selection
        for layer in plan.extraction_layers:
            is_selected = layer.id in selected_layer_ids
            layer.user_selected = is_selected
            if is_selected:
                selected_area_m2 += layer.area_m2
                selected_layer_names.append(layer.layer_name)

        # Also update JSON blob for backwards compatibility
        if plan.extraction_data:
            try:
                data = json.loads(plan.extraction_data)
                # Store layer names for backwards compatibility with old BOQ generation
                data["user_selected_layers"] = selected_layer_names
                data["user_confirmed_area"] = custom_area if custom_area else selected_area_m2
                data["extraction_reviewed"] = True
                plan.extraction_data = json.dumps(data, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

    db.commit()

    final_area = custom_area if custom_area else selected_area_m2

    # Start BOQ generation in background (still uses layer names for compatibility)
    background_tasks.add_task(
        generate_project_boq_background,
        project_id,
        set(selected_layer_names),  # Convert to set of names for BOQ generation
        custom_area,
        db
    )

    return {
        "message": "BOQ generation started",
        "project_id": project_id,
        "selected_layer_ids": list(selected_layer_ids),
        "selected_layer_names": selected_layer_names,
        "selected_area_m2": round(selected_area_m2, 2),
        "final_area_m2": round(final_area, 2),
        "custom_override": custom_area is not None,
        "status": "generating_boq"
    }


