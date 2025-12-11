"""
BOQ Items CRUD API
Allows users to edit, delete, and annotate BOQ line items
Also provides aggregation endpoints for multi-file BOQ
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import logging
from app.api import deps
from app import models, schemas, services
from app.services.ai_description_generator import get_ai_description_generator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{project_id}/boq/items", response_model=List[schemas.BOQItem])
def get_boq_items(
    project_id: int,
    include_deleted: bool = False,
    db: Session = Depends(deps.get_db)
):
    """Get all BOQ items for a project with source tracking"""
    query = db.query(models.BOQItem).filter(models.BOQItem.project_id == project_id)

    if not include_deleted:
        query = query.filter(models.BOQItem.is_deleted == False)

    items = query.order_by(models.BOQItem.chapter_code, models.BOQItem.item_code).all()
    return items


@router.patch("/{project_id}/boq/items/{item_id}", response_model=schemas.BOQItem)
def update_boq_item(
    project_id: int,
    item_id: int,
    update: schemas.BOQItemUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update BOQ item (quantity, price, notes)"""
    item = db.query(models.BOQItem).filter(
        models.BOQItem.id == item_id,
        models.BOQItem.project_id == project_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")

    # Update fields
    if update.quantity is not None:
        item.quantity = update.quantity
        item.is_modified = True

    if update.description_he is not None:
        item.description_he = update.description_he
        item.is_modified = True

    if update.unit_price is not None:
        item.unit_price = update.unit_price
        item.is_modified = True

    if update.user_notes is not None:
        item.user_notes = update.user_notes
        item.is_modified = True

    if update.is_deleted is not None:
        item.is_deleted = update.is_deleted

    # Recalculate total
    item.total_price = item.quantity * item.unit_price

    db.commit()
    db.refresh(item)
    return item


@router.post("/{project_id}/boq/items", response_model=schemas.BOQItem)
def create_boq_item(
    project_id: int,
    item_data: schemas.BOQItemCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new BOQ item in a chapter"""
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create new BOQ item
    new_item = models.BOQItem(
        project_id=project_id,
        plan_id=item_data.plan_id,
        chapter_code=item_data.chapter_code,
        chapter_name_he=item_data.chapter_name_he,
        chapter_name_en=item_data.chapter_name_en or "",
        item_code=item_data.item_code,
        description_he=item_data.description_he,
        description_en=item_data.description_en or "",
        quantity=item_data.quantity,
        unit=item_data.unit,
        unit_price=item_data.unit_price,
        total_price=item_data.total_price,
        source_filename=item_data.source_filename,
        source_layer=item_data.source_layer,
        confidence=item_data.confidence or 1.0,
        user_notes=item_data.user_notes,
        is_deleted=False,
        is_modified=True  # Mark as user-created
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@router.delete("/{project_id}/boq/items/{item_id}")
def delete_boq_item(
    project_id: int,
    item_id: int,
    db: Session = Depends(deps.get_db)
):
    """Soft delete BOQ item"""
    item = db.query(models.BOQItem).filter(
        models.BOQItem.id == item_id,
        models.BOQItem.project_id == project_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")

    item.is_deleted = True
    db.commit()

    return {"message": "Item deleted successfully"}


@router.post("/{project_id}/boq/items/{item_id}/ai-description")
def generate_ai_description_for_item(
    project_id: int,
    item_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Generate AI-enhanced description for a single BOQ item.

    Uses AI to create professional, detailed Hebrew description
    based on DWG layer data and Israeli construction standards (Dekel-style).
    """
    # Get BOQ item
    item = db.query(models.BOQItem).filter(
        models.BOQItem.id == item_id,
        models.BOQItem.project_id == project_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")

    # Get extraction layer data if available
    layer_data = None
    if item.plan_id and item.source_layer:
        extraction_layer = db.query(models.ProjectExtractionLayer).filter(
            models.ProjectExtractionLayer.plan_id == item.plan_id,
            models.ProjectExtractionLayer.layer_name == item.source_layer
        ).first()

        if extraction_layer:
            layer_data = {
                "area_m2": extraction_layer.area_m2,
                "polyline_count": extraction_layer.polyline_count,
                "hatch_count": extraction_layer.hatch_count,
            }

    # Generate AI description
    try:
        ai_generator = get_ai_description_generator()
        ai_result = ai_generator.generate_description(
            item_code=item.item_code,
            basic_description=item.description_he,
            layer_name=item.source_layer,
            quantity=item.quantity,
            unit=item.unit,
            chapter_code=item.chapter_code,
            chapter_name_he=item.chapter_name_he,
            area_m2=layer_data.get("area_m2") if layer_data else None,
            polyline_count=layer_data.get("polyline_count") if layer_data else None,
            hatch_count=layer_data.get("hatch_count") if layer_data else None,
        )

        # Update item with AI-generated description
        item.description_he = ai_result.get("description_he", item.description_he)
        if ai_result.get("description_en"):
            item.description_en = ai_result.get("description_en")

        # Store AI metadata in user_notes (or could create new field)
        ai_metadata = {
            "ai_generated": True,
            "ai_confidence": ai_result.get("confidence", 0.5),
            "technical_notes": ai_result.get("technical_notes", ""),
            "original_description": item.description_he  # Keep original for reference
        }
        if item.user_notes:
            # Try to parse existing notes as JSON, or keep as string
            try:
                existing_notes = json.loads(item.user_notes)
                if isinstance(existing_notes, dict):
                    existing_notes.update(ai_metadata)
                    item.user_notes = json.dumps(existing_notes, ensure_ascii=False)
                else:
                    item.user_notes = json.dumps(ai_metadata, ensure_ascii=False)
            except:
                # Not JSON, keep original and append AI metadata separately
                item.user_notes = json.dumps({
                    "user_note": item.user_notes,
                    **ai_metadata
                }, ensure_ascii=False)
        else:
            item.user_notes = json.dumps(ai_metadata, ensure_ascii=False)

        item.is_modified = True
        db.commit()
        db.refresh(item)

        logger.info(f"Generated AI description for BOQ item {item_id}")

        return {
            "success": True,
            "item_id": item_id,
            "description": ai_result.get("description_he"),
            "confidence": ai_result.get("confidence"),
            "technical_notes": ai_result.get("technical_notes")
        }

    except Exception as e:
        logger.error(f"Failed to generate AI description for item {item_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI description: {str(e)}"
        )


@router.post("/{project_id}/boq/items/ai-descriptions/batch")
def generate_ai_descriptions_batch(
    project_id: int,
    item_ids: Optional[List[int]] = None,
    db: Session = Depends(deps.get_db)
):
    """
    Generate AI-enhanced descriptions for multiple BOQ items.

    If item_ids is provided, only generates for those items.
    If item_ids is None, generates for all items in the project.

    Returns summary of generation results.
    """
    # Get project
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get items to process
    query = db.query(models.BOQItem).filter(models.BOQItem.project_id == project_id)

    if item_ids:
        query = query.filter(models.BOQItem.id.in_(item_ids))

    items = query.all()

    if not items:
        return {
            "success": True,
            "processed": 0,
            "message": "No items to process"
        }

    logger.info(f"Starting batch AI description generation for {len(items)} items")

    # Get extraction layers for all plans in project
    extraction_layers_map = {}
    plan_ids = list(set([item.plan_id for item in items if item.plan_id]))

    if plan_ids:
        extraction_layers = db.query(models.ProjectExtractionLayer).filter(
            models.ProjectExtractionLayer.plan_id.in_(plan_ids)
        ).all()

        for layer in extraction_layers:
            key = f"{layer.plan_id}_{layer.layer_name}"
            extraction_layers_map[key] = {
                "area_m2": layer.area_m2,
                "polyline_count": layer.polyline_count,
                "hatch_count": layer.hatch_count,
            }

    # Generate AI descriptions
    ai_generator = get_ai_description_generator()
    success_count = 0
    error_count = 0
    errors = []

    for item in items:
        try:
            # Get layer data
            layer_data = None
            if item.plan_id and item.source_layer:
                key = f"{item.plan_id}_{item.source_layer}"
                layer_data = extraction_layers_map.get(key)

            # Generate AI description
            ai_result = ai_generator.generate_description(
                item_code=item.item_code,
                basic_description=item.description_he,
                layer_name=item.source_layer,
                quantity=item.quantity,
                unit=item.unit,
                chapter_code=item.chapter_code,
                chapter_name_he=item.chapter_name_he,
                area_m2=layer_data.get("area_m2") if layer_data else None,
                polyline_count=layer_data.get("polyline_count") if layer_data else None,
                hatch_count=layer_data.get("hatch_count") if layer_data else None,
            )

            # Update item
            item.description_he = ai_result.get("description_he", item.description_he)
            if ai_result.get("description_en"):
                item.description_en = ai_result.get("description_en")

            # Store AI metadata
            ai_metadata = {
                "ai_generated": True,
                "ai_confidence": ai_result.get("confidence", 0.5),
                "technical_notes": ai_result.get("technical_notes", ""),
            }
            item.user_notes = json.dumps(ai_metadata, ensure_ascii=False)
            item.is_modified = True

            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append({
                "item_id": item.id,
                "item_code": item.item_code,
                "error": str(e)
            })
            logger.error(f"Failed to generate AI description for item {item.id}: {e}")

    # Commit all changes
    db.commit()

    logger.info(f"Batch AI description generation complete: {success_count} success, {error_count} errors")

    return {
        "success": True,
        "total_items": len(items),
        "processed": success_count,
        "errors": error_count,
        "error_details": errors if errors else None
    }


# =============================================================================
# BOQ Aggregation Endpoints
# =============================================================================

@router.get("/{project_id}/boq/aggregated")
def get_aggregated_boq(
    project_id: int,
    include_deleted: bool = False,
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get aggregated BOQ for a project, combining items from all plan files.

    This endpoint:
    - Deduplicates items by item_code
    - Sums quantities for matching items across files
    - Tracks which source files contributed to each item
    - Organizes items by chapter

    Returns:
        Aggregated BOQ with chapters, items, and summary statistics
    """
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return services.get_aggregated_boq(db, project_id, include_deleted)


@router.get("/{project_id}/boq/by-plan")
def get_boq_by_plan(
    project_id: int,
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get BOQ grouped by source plan/file.

    Useful for viewing BOQ contributions from each individual file
    before aggregation.

    Returns:
        BOQ data organized by source plan file
    """
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return services.get_boq_by_plan(db, project_id)


@router.get("/{project_id}/boq/chapter-summary")
def get_chapter_summary(
    project_id: int,
    db: Session = Depends(deps.get_db)
) -> List[Dict[str, Any]]:
    """
    Get summary of BOQ by chapter for a project.

    Provides a quick overview of chapter totals without full item details.

    Returns:
        List of chapter summaries with totals
    """
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return services.get_chapter_summary(db, project_id)
