"""
AI Engine for ConstructionAI Pro

Orchestrates the extraction of material quantities from various file formats:
- PDF (construction plans, BOQ documents)
- DXF/DWG (CAD drawings)
- IFC (BIM models)
- Images (scanned plans)
"""

import os
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from app import models
from app.services.extraction import extract_from_pdf, extract_from_dxf, extract_from_ifc

logger = logging.getLogger(__name__)

# Supported file extensions and their extractors
EXTRACTORS = {
    '.pdf': extract_from_pdf,
    '.dxf': extract_from_dxf,
    '.dwg': extract_from_dxf,  # DWG routes to DXF extractor
    '.ifc': extract_from_ifc,
    # Image formats - route to PDF extractor which handles images via Vision API
    '.png': extract_from_pdf,
    '.jpg': extract_from_pdf,
    '.jpeg': extract_from_pdf,
    '.bmp': extract_from_pdf,
    '.tiff': extract_from_pdf,
}


def process_plan(plan_id: int, db: Session) -> List[Dict]:
    """
    Process a construction plan and extract material quantities.

    Routes to the appropriate extractor based on file type,
    updates progress during processing, and saves results to database.

    Args:
        plan_id: ID of the plan to process
        db: Database session

    Returns:
        List of extracted materials
    """
    plan = db.query(models.ProjectPlan).filter(models.ProjectPlan.id == plan_id).first()
    if not plan:
        logger.error(f"Plan {plan_id} not found")
        return []

    logger.info(f"Starting processing for plan {plan_id}: {plan.filename}")

    try:
        # Update status to processing
        _update_progress(plan, db, "processing", 10)

        file_path = plan.file_path
        file_ext = os.path.splitext(file_path)[1].lower()

        logger.info(f"File type: {file_ext}")
        _update_progress(plan, db, "processing", 20)

        # Get appropriate extractor
        extractor = EXTRACTORS.get(file_ext)

        if not extractor:
            logger.warning(f"No extractor available for {file_ext}")
            materials_data = [{
                "material_name": f"Unknown Format ({file_ext}) - Manual Review Required",
                "quantity": 0,
                "unit": "N/A",
                "confidence_score": 0.0
            }]
        else:
            logger.info(f"Using extractor: {extractor.__name__}")
            _update_progress(plan, db, "processing", 30)

            # Run extraction
            materials_data = extractor(file_path)

            logger.info(f"Extracted {len(materials_data)} materials")

        _update_progress(plan, db, "processing", 70)

        # Save to database (filter to only include DB model fields)
        saved_count = 0
        for mat_data in materials_data:
            # Only include fields that exist in the MaterialQuantity model
            filtered_data = {
                'material_name': mat_data.get('material_name', 'Unknown'),
                'quantity': float(mat_data.get('quantity', 0)),
                'unit': mat_data.get('unit', 'N/A'),
                'confidence_score': float(mat_data.get('confidence_score', 0.5))
            }

            material = models.MaterialQuantity(
                plan_id=plan_id,
                **filtered_data
            )
            db.add(material)
            saved_count += 1

        logger.info(f"Saved {saved_count} materials to database")
        _update_progress(plan, db, "processing", 90)

        # Mark as completed
        _update_progress(plan, db, "completed", 100)

        logger.info(f"Processing complete for plan {plan_id}")
        return materials_data

    except Exception as e:
        logger.error(f"Processing failed for plan {plan_id}: {e}")
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise


def _update_progress(plan: models.ProjectPlan, db: Session, status: str, progress: int):
    """Update plan processing status and progress"""
    plan.processing_status = status
    plan.processing_progress = progress
    db.commit()
