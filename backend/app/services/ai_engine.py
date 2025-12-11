"""
AI Engine for ConstructionAI Pro

Orchestrates the extraction of material quantities from various file formats:
- DXF/DWG (CAD drawings) - Uses AutoCAD COM + Dekel pricing
- PDF (Construction plans) - Uses Vision AI (Gemini/OpenAI/Claude/Ollama)

NEW FLOW (Dec 2024):
1. process_plan() - ONLY extracts data, saves area_by_layer, status="extracted"
2. User reviews extraction results and selects layers
3. generate_boq_for_plan() - Generates BOQ after user confirms selection

PDF FLOW (Dec 2024):
1. process_pdf_plan() - Uses Vision AI to extract from PDF images
2. User reviews extraction results
3. generate_boq_for_plan() - Generates BOQ from extracted data

NO FALLBACKS - If extraction fails, an error is thrown.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from app import models
from app.services.extraction.dwg_extractor import extract_raw_data_from_dwg, categorize_layer
from app.services.extraction.pdf_extractor import (
    extract_from_pdf_detailed,
    PlanType,
    PDFExtractionError
)
from app.services.boq.israeli_boq_service import IsraeliBOQService

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {'.dwg', '.dxf', '.pdf'}
CAD_EXTENSIONS = {'.dwg', '.dxf'}
PDF_EXTENSIONS = {'.pdf'}


class ExtractionError(Exception):
    """Raised when extraction fails"""
    pass


class UnsupportedFileTypeError(Exception):
    """Raised when file type is not supported"""
    pass


def process_plan(plan_id: int, db: Session, plan_type: str = "general") -> Dict:
    """
    Process a construction plan - EXTRACTION ONLY.

    This function:
    1. Extracts raw data from AutoCAD file or PDF
    2. Saves extraction data including area_by_layer
    3. Sets status to "extracted" (waiting for user review)

    BOQ generation happens separately after user confirms layer selection.

    Args:
        plan_id: ID of the plan to process
        db: Database session
        plan_type: Type of plan for PDF extraction (architectural, electrical, etc.)

    Returns:
        Dict with extraction summary

    Raises:
        ExtractionError: If extraction fails
        UnsupportedFileTypeError: If file type is not supported
    """
    plan = db.query(models.ProjectPlan).filter(models.ProjectPlan.id == plan_id).first()
    if not plan:
        raise ExtractionError(f"Plan {plan_id} not found")

    logger.info(f"Starting EXTRACTION for plan {plan_id}: {plan.filename}")

    try:
        # Update status to processing
        _update_progress(plan, db, "processing", 10)

        file_path = plan.file_path
        file_ext = os.path.splitext(file_path)[1].lower()

        logger.info(f"File type: {file_ext}")

        # Check if file type is supported
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"File type '{file_ext}' is not supported. "
                f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        _update_progress(plan, db, "processing", 30)

        # Route to appropriate extractor based on file type
        if file_ext in PDF_EXTENSIONS:
            # Use Vision AI for PDF extraction
            return _process_pdf_plan(plan, db, plan_type)

        # Extract raw data from AutoCAD (DWG/DXF)
        logger.info("Extracting data from AutoCAD file...")
        raw_data = extract_raw_data_from_dwg(file_path)

        if not raw_data.get('extraction_success', False):
            errors = raw_data.get('errors', ['Unknown extraction error'])
            raise ExtractionError(
                f"Failed to extract data from {plan.filename}: {'; '.join(errors)}"
            )

        logger.info(f"Extracted raw data: {len(raw_data.get('blocks', []))} blocks, "
                   f"{len(raw_data.get('text_entities', []))} text items, "
                   f"{len(raw_data.get('layers', {}))} layers")

        _update_progress(plan, db, "processing", 70)

        # Detect drawing units FIRST for consistent conversion
        boq_service = IsraeliBOQService()
        detected_unit = boq_service._detect_drawing_units(raw_data)

        # Set conversion factor based on detected units
        if detected_unit == "cm":
            area_divisor = 10_000  # cm² → m²
        elif detected_unit == "mm":
            area_divisor = 1_000_000  # mm² → m²
        else:
            area_divisor = 1  # Already in m²

        logger.info(f"Detected drawing units: {detected_unit}, area divisor: {area_divisor}")

        # Convert raw area values to m² for storage
        geometry = raw_data.get('geometry', {})
        raw_total_area = geometry.get("total_area", 0)
        total_area_m2 = raw_total_area / area_divisor

        # Convert area_by_layer values to m²
        raw_area_by_layer = raw_data.get("area_by_layer", {})
        converted_area_by_layer = {}
        for layer_name, layer_data in raw_area_by_layer.items():
            converted_area_by_layer[layer_name] = {
                "area": layer_data.get("area", 0.0) / area_divisor,  # Convert to m²
                "polyline_count": layer_data.get("polyline_count", 0),
                "hatch_count": layer_data.get("hatch_count", 0),
            }

        # Save FULL extraction data including CONVERTED area_by_layer for user review
        extraction_data = {
            "extraction_method": raw_data.get("extraction_method", "unknown"),
            "blocks_count": len(raw_data.get("blocks", [])),
            "text_count": len(raw_data.get("text_entities", [])),
            "layers_count": len(raw_data.get("layers", {})),
            "total_area_m2": total_area_m2,  # Now in m²
            "total_area_raw": raw_total_area,  # Original raw value
            "total_perimeter_cm": geometry.get("total_perimeter", 0),
            "polylines_count": geometry.get("polyline_count", 0),
            "circles_count": geometry.get("circle_count", 0),
            "arcs_count": geometry.get("arc_count", 0),
            "hatch_count": geometry.get("hatch_count", 0),
            "block_scales": raw_data.get("block_scales", []),
            "detected_units": detected_unit,  # Store the detected unit
            "area_divisor": area_divisor,  # Store the conversion factor
            # KEY: Per-layer area data for user selection (NOW CONVERTED TO m²!)
            "area_by_layer": converted_area_by_layer,
            "closed_polylines": raw_data.get("closed_polylines", []),
            # Track review status
            "extraction_reviewed": False,
            "user_selected_layers": None,
            "user_confirmed_area": None,
        }
        plan.extraction_data = json.dumps(extraction_data, ensure_ascii=False)
        db.commit()
        logger.info(f"Saved extraction data with {len(extraction_data.get('area_by_layer', {}))} layers to plan {plan_id} (total: {total_area_m2:.2f} m²)")

        # Also save extraction layers to the new DB table for better querying
        # Use the already-converted area_by_layer data
        if converted_area_by_layer:
            # Clear any existing extraction layers for this plan
            db.query(models.ProjectExtractionLayer).filter(
                models.ProjectExtractionLayer.plan_id == plan_id
            ).delete()

            # Create new extraction layer records (area already converted to m²)
            for layer_name, layer_data in converted_area_by_layer.items():
                extraction_layer = models.ProjectExtractionLayer(
                    plan_id=plan_id,
                    layer_name=layer_name,
                    area_m2=layer_data.get("area", 0.0),  # Already in m²
                    polyline_count=layer_data.get("polyline_count", 0),
                    hatch_count=layer_data.get("hatch_count", 0),
                    auto_category=categorize_layer(layer_name),
                    user_selected=None  # Will be set by user during review
                )
                db.add(extraction_layer)

            db.commit()
            logger.info(f"Saved {len(converted_area_by_layer)} extraction layers to DB for plan {plan_id}")

        # Mark as "extracted" - waiting for user to review and confirm
        _update_progress(plan, db, "extracted", 100)

        logger.info(f"Extraction complete for plan {plan_id} - waiting for user review")
        return extraction_data

    except (ExtractionError, UnsupportedFileTypeError):
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise
    except Exception as e:
        logger.error(f"Extraction failed for plan {plan_id}: {e}")
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise ExtractionError(f"Extraction failed: {str(e)}")


def generate_boq_for_plan(
    plan_id: int,
    db: Session,
    selected_layers: Optional[Set[str]] = None,
    custom_area_m2: Optional[float] = None
) -> List[Dict]:
    """
    Generate BOQ for a plan AFTER user confirms extraction selection.

    This function:
    1. Loads extraction data
    2. Filters area based on selected layers (or uses custom area)
    3. Generates BOQ with AI + Dekel pricing
    4. Saves BOQ data and marks as completed

    Args:
        plan_id: ID of the plan
        db: Database session
        selected_layers: Set of layer names to include (if None, uses stored selection)
        custom_area_m2: Override area in m² (if provided, ignores layers)

    Returns:
        List of material data from BOQ

    Raises:
        ExtractionError: If BOQ generation fails
    """
    plan = db.query(models.ProjectPlan).filter(models.ProjectPlan.id == plan_id).first()
    if not plan:
        raise ExtractionError(f"Plan {plan_id} not found")

    if not plan.extraction_data:
        raise ExtractionError(f"Plan {plan_id} has no extraction data. Run extraction first.")

    logger.info(f"Starting BOQ generation for plan {plan_id}: {plan.filename}")

    # Get project name if available
    project_name = None
    if plan.project:
        project_name = plan.project.name

    try:
        # Update status to generating BOQ
        _update_progress(plan, db, "generating_boq", 10)

        # Load extraction data
        extraction_data = json.loads(plan.extraction_data)
        area_by_layer = extraction_data.get("area_by_layer", {})

        # Determine which layers to use
        if selected_layers is None:
            # Use stored selection from user confirmation
            stored_layers = extraction_data.get("user_selected_layers")
            if stored_layers:
                selected_layers = set(stored_layers)
            else:
                # Default: use all layers
                selected_layers = set(area_by_layer.keys())

        # Calculate final area
        if custom_area_m2 is not None:
            final_area_m2 = custom_area_m2
            logger.info(f"Using custom area override: {final_area_m2} m²")
        else:
            # Sum area from selected layers
            final_area_m2 = 0.0
            for layer_name, layer_data in area_by_layer.items():
                if layer_name in selected_layers:
                    final_area_m2 += layer_data.get("area", 0.0)
            logger.info(f"Calculated area from {len(selected_layers)} selected layers: {final_area_m2:.2f} m²")

        _update_progress(plan, db, "generating_boq", 30)

        # Re-extract raw data for BOQ generation (need full data)
        # TODO: In future, store raw_data to avoid re-extraction
        raw_data = extract_raw_data_from_dwg(plan.file_path)

        if not raw_data.get('extraction_success', False):
            raise ExtractionError(f"Failed to re-extract data for BOQ generation")

        _update_progress(plan, db, "generating_boq", 50)

        # Generate Israeli BOQ with AI + Dekel pricing
        logger.info("Generating BOQ with AI + Dekel pricing...")
        boq_service = IsraeliBOQService()
        boq = boq_service.generate_boq_from_raw_data(
            raw_data=raw_data,
            filename=plan.filename,
            project_name=project_name,
            override_area_m2=final_area_m2  # Pass the user-confirmed area
        )
        boq_dict = boq_service.boq_to_dict(boq)

        logger.info(f"Generated BOQ with {len(boq.chapters)} chapters, "
                   f"Grand Total: {boq.grand_total:,.2f} ILS")

        _update_progress(plan, db, "generating_boq", 70)

        # Save full BOQ data to plan
        plan.boq_data = json.dumps(boq_dict, ensure_ascii=False)
        plan.boq_subtotal = boq.subtotal
        plan.boq_vat_amount = boq.vat_amount
        plan.boq_grand_total = boq.grand_total

        # Update extraction data with confirmation
        extraction_data["extraction_reviewed"] = True
        extraction_data["user_selected_layers"] = list(selected_layers)
        extraction_data["user_confirmed_area"] = final_area_m2
        plan.extraction_data = json.dumps(extraction_data, ensure_ascii=False)
        db.commit()

        # Save BOQ items to database with source tracking
        logger.info("Saving BOQ items to database with source tracking...")
        boq_service.save_boq_to_database(
            project_id=plan.project_id,
            plan_id=plan.id,
            boq=boq,
            selected_layers=list(selected_layers),
            db=db
        )

        _update_progress(plan, db, "generating_boq", 80)

        # Convert BOQ items to materials for database storage
        materials_data = []
        for chapter in boq.chapters:
            for item in chapter.items:
                materials_data.append({
                    'material_name': item.description_he,
                    'quantity': item.quantity,
                    'unit': item.unit,
                    'confidence_score': item.confidence,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price,
                    'dekel_code': item.dekel_code,
                    'chapter': chapter.chapter_name_he
                })

        # Save materials to database
        saved_count = 0
        for mat_data in materials_data:
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
        _update_progress(plan, db, "generating_boq", 90)

        # Mark as completed
        _update_progress(plan, db, "completed", 100)

        logger.info(f"BOQ generation complete for plan {plan_id}")
        return materials_data

    except ExtractionError:
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise
    except Exception as e:
        logger.error(f"BOQ generation failed for plan {plan_id}: {e}")
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise ExtractionError(f"BOQ generation failed: {str(e)}")


def _update_progress(plan: models.ProjectPlan, db: Session, status: str, progress: int):
    """Update plan processing status and progress"""
    plan.processing_status = status
    plan.processing_progress = progress
    db.commit()


def _process_pdf_plan(plan: models.ProjectPlan, db: Session, plan_type: str = "general") -> Dict:
    """
    Process a PDF plan using Vision AI extraction.

    Args:
        plan: The ProjectPlan model instance
        db: Database session
        plan_type: Type of plan (architectural, electrical, plumbing, etc.)

    Returns:
        Dict with extraction results
    """
    logger.info(f"Processing PDF plan {plan.id}: {plan.filename} as type '{plan_type}'")

    try:
        _update_progress(plan, db, "processing", 40)

        # Extract data using Vision AI
        logger.info(f"Using Vision AI to extract from PDF (type: {plan_type})...")
        extraction_result = extract_from_pdf_detailed(plan.file_path, plan_type)

        _update_progress(plan, db, "processing", 70)

        logger.info(f"PDF extraction complete. Provider: {extraction_result.get('provider_used')}, "
                   f"Pages: {extraction_result.get('pages_processed')}")

        # Convert PDF extraction result to standard extraction_data format
        summary = extraction_result.get("summary", {})
        all_items = extraction_result.get("all_items", [])

        # Calculate total area from extracted items (if available)
        total_area_m2 = 0.0
        area_by_category = {}

        for item in all_items:
            if isinstance(item, dict):
                area = item.get("area_m2", 0)
                if area:
                    total_area_m2 += area
                    category = item.get("type", item.get("name", "general"))
                    if category not in area_by_category:
                        area_by_category[category] = {"area": 0.0, "count": 0}
                    area_by_category[category]["area"] += area
                    area_by_category[category]["count"] += 1

        # Build extraction data in standard format
        extraction_data = {
            "extraction_method": f"vision_ai_{extraction_result.get('provider_used', 'unknown').lower()}",
            "plan_type": plan_type,
            "source_file": extraction_result.get("source_file", plan.filename),
            "pages_processed": extraction_result.get("pages_processed", 1),
            "provider_used": extraction_result.get("provider_used", "unknown"),

            # Area data (may be estimated from Vision AI)
            "total_area_m2": total_area_m2,
            "area_by_category": area_by_category,

            # PDF-specific: no layer data like CAD files
            "area_by_layer": {},
            "layers_count": 0,

            # Extracted items from Vision AI
            "extracted_items": all_items,
            "items_count": len(all_items),

            # Raw pages data for detailed review
            "pages": extraction_result.get("pages", []),

            # Summary statistics
            "summary": summary,

            # Confidence from extraction
            "confidence": _calculate_pdf_confidence(extraction_result),

            # Track review status
            "extraction_reviewed": False,
            "user_confirmed_area": None,
        }

        # Save extraction data
        plan.extraction_data = json.dumps(extraction_data, ensure_ascii=False)
        db.commit()

        logger.info(f"Saved PDF extraction data for plan {plan.id}: "
                   f"{len(all_items)} items, {total_area_m2:.2f} m² estimated")

        _update_progress(plan, db, "extracted", 100)

        logger.info(f"PDF extraction complete for plan {plan.id} - waiting for user review")
        return extraction_data

    except PDFExtractionError as e:
        logger.error(f"PDF extraction failed for plan {plan.id}: {e}")
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise ExtractionError(f"PDF extraction failed: {str(e)}")
    except Exception as e:
        logger.error(f"PDF extraction failed for plan {plan.id}: {e}")
        _update_progress(plan, db, "failed", plan.processing_progress)
        raise ExtractionError(f"PDF extraction failed: {str(e)}")


def _calculate_pdf_confidence(extraction_result: Dict) -> float:
    """Calculate overall confidence from PDF extraction result"""
    pages = extraction_result.get("pages", [])
    if not pages:
        return 0.5

    confidences = []
    for page in pages:
        if isinstance(page, dict):
            conf = page.get("confidence", 0.5)
            if isinstance(conf, (int, float)):
                confidences.append(conf)

    if not confidences:
        return 0.5

    return sum(confidences) / len(confidences)


def get_supported_plan_types() -> List[Dict]:
    """Get list of supported plan types for PDF extraction"""
    return [
        {"value": "architectural", "label": "תכנית אדריכלית / בנייה", "label_en": "Architectural / Construction"},
        {"value": "electrical", "label": "תכנית חשמל", "label_en": "Electrical"},
        {"value": "plumbing", "label": "תכנית אינסטלציה", "label_en": "Plumbing"},
        {"value": "structural", "label": "תכנית קונסטרוקציה", "label_en": "Structural"},
        {"value": "hvac", "label": "תכנית מיזוג אוויר", "label_en": "HVAC"},
        {"value": "windows_doors", "label": "לוח חלונות ודלתות", "label_en": "Windows & Doors"},
        {"value": "finishing", "label": "תכנית גמרים", "label_en": "Finishing"},
        {"value": "landscape", "label": "תכנית גינון", "label_en": "Landscape"},
        {"value": "general", "label": "תכנית כללית", "label_en": "General"},
    ]
