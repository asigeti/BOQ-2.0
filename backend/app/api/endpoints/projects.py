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
from app.models.boq_hierarchy import (
    get_or_create_sub_document,
    get_or_create_chapter,
    get_or_create_sub_chapter,
    update_hierarchy_totals
)

router = APIRouter()


def scan_folder_for_plan_files(folder_path: str) -> List[str]:
    """
    Recursively scan a folder for plan files (DWG, DXF, PDF).
    Returns list of absolute paths to plan files.
    """
    plan_files = []
    folder = Path(folder_path)

    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")

    if not folder.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")

    # Recursively find all .dwg files
    for dwg_file in folder.rglob("*.dwg"):
        plan_files.append(str(dwg_file.absolute()))

    # Also check for .dxf files
    for dxf_file in folder.rglob("*.dxf"):
        plan_files.append(str(dxf_file.absolute()))

    # Also check for .pdf files
    for pdf_file in folder.rglob("*.pdf"):
        plan_files.append(str(pdf_file.absolute()))

    return sorted(plan_files)


# Backwards compatibility alias
def scan_folder_for_dwg(folder_path: str) -> List[str]:
    """Alias for scan_folder_for_plan_files for backwards compatibility."""
    return scan_folder_for_plan_files(folder_path)


def process_project_files(project_id: int):
    """
    Background task to EXTRACT data from all plan files in a project.

    FLOW by file type:
    - DWG/DXF: Extract layers -> User selects layers -> Generate BOQ
    - PDF: Extract with Vision AI -> Generate BOQ directly (no layer selection)

    For PDF-only projects, BOQ is generated immediately after extraction.
    For mixed or DWG-only projects, waits for user layer selection.

    NOTE: This function creates its own database session because it runs
    as a background task after the endpoint returns. The session from
    the endpoint would be closed by then.
    """
    import logging
    import traceback
    from app.db.session import SessionLocal

    logger = logging.getLogger(__name__)

    # Create a new session for the background task
    db = SessionLocal()

    try:
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

            # Track file types for flow decision
            has_cad_files = False
            has_pdf_files = False
            pdf_plans = []

            for plan in plans:
                try:
                    file_ext = os.path.splitext(plan.filename)[1].lower()
                    logger.info(f"Extracting plan {plan.id}: {plan.filename} (type: {file_ext})")

                    # Track file types
                    if file_ext in {'.dwg', '.dxf'}:
                        has_cad_files = True
                    elif file_ext == '.pdf':
                        has_pdf_files = True
                        pdf_plans.append(plan)

                    # Auto-detect plan type for PDFs based on filename
                    plan_type = "general"
                    if file_ext == '.pdf':
                        plan_type = _detect_pdf_plan_type(plan.filename)
                        logger.info(f"Auto-detected plan type: {plan_type}")

                    # Extract data only (no BOQ generation)
                    services.process_plan(plan.id, db, plan_type=plan_type)
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

            # Determine next step based on file types
            logger.info(f"Project {project_id}: has_cad_files={has_cad_files}, has_pdf_files={has_pdf_files}, pdf_plans={len(pdf_plans)}")
            if has_cad_files:
                # Has DWG/DXF files - need layer selection
                project.processing_status = "extracted"
                project.processing_progress = 100
                db.commit()
                logger.info(f"Project {project_id} extraction completed - waiting for user layer selection")
            else:
                # PDF-only project - generate BOQ directly from extracted items
                logger.info(f"Project {project_id} is PDF-only - generating BOQ directly")
                project.processing_status = "generating_boq"
                db.commit()

                try:
                    _generate_boq_from_pdf_extractions(project_id, pdf_plans, db)
                    project.processing_status = "completed"
                    project.processing_progress = 100
                    db.commit()
                    logger.info(f"Project {project_id} PDF BOQ generation completed")
                except Exception as e:
                    logger.error(f"PDF BOQ generation failed: {e}")
                    logger.error(traceback.format_exc())
                    project.processing_status = "failed"
                    db.commit()

        except Exception as e:
            logger.error(f"Project {project_id} extraction failed: {e}")
            logger.error(traceback.format_exc())
            project.processing_status = "failed"
            db.commit()

    finally:
        # Always close the session when done
        db.close()
        logger.info(f"Background task session closed for project {project_id}")


def _generate_boq_from_pdf_extractions(project_id: int, pdf_plans: list, db: Session):
    """
    Generate BOQ items directly from PDF extraction results.

    Creates proper 4-level Israeli BOQ hierarchy:
    - תת כתב (Sub-Document) - Level 1
    - פרק (Chapter) - Level 2
    - תת פרק (Sub-Chapter) - Level 3
    - סעיף (Item) - Level 4

    Includes:
    - Automatic Dekel pricing lookup for extracted items
    - Professional 4-level item code structure (תת_כתב.פרק.תת_פרק.סעיף)
    - Smart categorization to sub-chapters based on description
    """
    import logging
    from app.services.pricing.dekel_pricing import DekelPricing
    logger = logging.getLogger(__name__)

    logger.info(f"Generating BOQ from {len(pdf_plans)} PDF plans for project {project_id}")

    # Initialize Dekel pricing service for price lookup
    dekel_pricing = DekelPricing()

    # =========================================================================
    # Create default תת כתב (Sub-Document) for the project
    # =========================================================================
    # Determine the sub-document code based on plan types
    # Default to "1" for general projects
    sub_doc_code = "1"
    sub_doc_name = "כתב כמויות ראשי"

    # Check plan types to determine appropriate sub-document
    for plan in pdf_plans:
        if plan.extraction_data:
            try:
                extraction_data = json.loads(plan.extraction_data)
                plan_type = extraction_data.get("plan_type", "general")
                if plan_type in ["site_development", "landscape"]:
                    sub_doc_code = "13"
                    sub_doc_name = "פיתוח שטח"
                elif plan_type == "traffic":
                    sub_doc_code = "14"
                    sub_doc_name = "עבודות תנועה"
                break  # Use first plan's type
            except:
                pass

    sub_document = get_or_create_sub_document(
        db, project_id, sub_doc_code, sub_doc_name
    )
    logger.info(f"Created/got sub-document: {sub_doc_code} - {sub_doc_name}")

    # =========================================================================
    # Cache for created hierarchy objects (avoid duplicates)
    # =========================================================================
    chapter_cache = {}  # (sub_doc_id, chapter_code) -> BOQChapter
    sub_chapter_cache = {}  # (chapter_id, sub_chapter_code) -> BOQSubChapter

    # Track item counts per sub-chapter/section for 4-level codes
    # Key: (chapter_code, sub_chapter, section) -> item_num
    subchapter_counters = {}

    # Track all created sub-chapters for total updates
    created_sub_chapter_ids = set()

    for plan in pdf_plans:
        try:
            if not plan.extraction_data:
                logger.warning(f"Plan {plan.id} has no extraction data")
                continue

            extraction_data = json.loads(plan.extraction_data)
            extracted_items = extraction_data.get("extracted_items", [])
            plan_type = extraction_data.get("plan_type", "general")
            confidence = extraction_data.get("confidence", 0.5)

            logger.info(f"Processing plan {plan.id}: {len(extracted_items)} items, type={plan_type}")

            # Get chapter info for this plan type
            chapter_info = _get_chapter_for_plan_type(plan_type)
            chapter_code = chapter_info["code"]

            # =========================================================================
            # Get or create פרק (Chapter) for this plan type
            # =========================================================================
            chapter_key = (sub_document.id, chapter_code)
            if chapter_key not in chapter_cache:
                chapter = get_or_create_chapter(
                    db,
                    sub_document.id,
                    chapter_code,
                    chapter_info["name_he"],
                    chapter_info.get("name_en", ""),
                    chapter_code  # dekel_code same as chapter_code
                )
                chapter_cache[chapter_key] = chapter
                logger.info(f"Created/got chapter: {chapter_code} - {chapter_info['name_he']}")
            else:
                chapter = chapter_cache[chapter_key]

            # Convert extracted items to BOQ items
            for item in extracted_items:
                if not isinstance(item, dict):
                    continue

                # Get quantity - use 1 as default if not found/zero
                quantity = _get_item_quantity(item)
                needs_quantity_review = False
                if quantity <= 0:
                    quantity = 1.0  # Default quantity for review
                    needs_quantity_review = True
                    logger.info(f"Item with zero quantity, defaulting to 1: {item.get('description', item.get('type', 'unknown'))[:50]}")

                # Get item description and unit
                description = _get_item_description(item)
                unit = item.get("unit", "יח׳")

                # Categorize item to sub-chapter and section for 4-level code
                sub_chapter_code, section = _categorize_item_to_subchapter(description, chapter_code)

                # =========================================================================
                # Get or create תת פרק (Sub-Chapter)
                # =========================================================================
                sub_chapter_key = (chapter.id, sub_chapter_code)
                if sub_chapter_key not in sub_chapter_cache:
                    sub_chapter_name = _get_sub_chapter_name(chapter_code, sub_chapter_code)
                    sub_chapter = get_or_create_sub_chapter(
                        db,
                        chapter.id,
                        sub_chapter_code,
                        sub_chapter_name
                    )
                    sub_chapter_cache[sub_chapter_key] = sub_chapter
                    logger.info(f"Created/got sub-chapter: {sub_chapter_code} - {sub_chapter_name}")
                else:
                    sub_chapter = sub_chapter_cache[sub_chapter_key]

                created_sub_chapter_ids.add(sub_chapter.id)

                # Get next item number for this sub-chapter/section
                counter_key = (chapter_code, sub_chapter_code, section)
                if counter_key not in subchapter_counters:
                    subchapter_counters[counter_key] = 0
                subchapter_counters[counter_key] += 1
                item_num = subchapter_counters[counter_key]

                # Generate professional 4-level item code
                full_item_code = f"{sub_doc_code}.{chapter_code.lstrip('0') or '0'}.{sub_chapter_code}.{item_num:04d}"
                section_code = f"{item_num:04d}"

                # Try to get unit price from extraction first, then from Dekel pricing
                unit_price = float(item.get("unit_price", 0) or 0)
                item_confidence = confidence
                user_note = None
                has_dekel_price = False

                if unit_price == 0:
                    # Try to match with Dekel pricing
                    price_match = dekel_pricing.fuzzy_match_description(description, unit)
                    if price_match:
                        unit_price = price_match.price
                        has_dekel_price = True
                        logger.info(f"Matched '{description[:30]}...' to Dekel: {price_match.name_he} @ {unit_price} ILS")
                    else:
                        # No Dekel price found - try AI estimation
                        logger.info(f"No Dekel price for '{description[:30]}...' - trying AI estimation")
                        ai_price, ai_conf, ai_note = _estimate_price_with_ai(description, unit, quantity)

                        if ai_price > 0:
                            unit_price = ai_price
                            item_confidence = ai_conf  # AI estimates have lower confidence
                            user_note = ai_note  # Shows "💡 אומדן AI: <reasoning>"
                            logger.info(f"AI estimated '{description[:30]}...': {ai_price} ILS ({ai_note})")
                        else:
                            # AI estimation also failed - flag for manual review
                            item_confidence = min(item_confidence, 0.3)  # Very low confidence
                            user_note = ai_note or "⚠️ לא נמצא מחיר - נדרש תמחור ידני"
                            logger.warning(f"No price found for: '{description[:40]}...' ({unit})")
                else:
                    has_dekel_price = True

                # Add quantity review note if needed
                if needs_quantity_review:
                    quantity_note = "📐 כמות לא נמצאה - נא לעדכן ידנית"
                    if user_note:
                        user_note = f"{quantity_note} | {user_note}"
                    else:
                        user_note = quantity_note
                    item_confidence = min(item_confidence, 0.4)  # Lower confidence for items needing review

                # Create BOQ item with proper hierarchy linkage
                boq_item = models.BOQItem(
                    project_id=project_id,
                    plan_id=plan.id,
                    # NEW: Hierarchical structure linkage
                    sub_chapter_id=sub_chapter.id,
                    section_code=section_code,
                    full_item_code=full_item_code,
                    # Legacy fields (for backward compatibility)
                    chapter_code=chapter_code,
                    chapter_name_he=chapter_info["name_he"],
                    chapter_name_en=chapter_info.get("name_en", ""),
                    item_code=full_item_code,
                    # Item details
                    description_he=description,
                    description_en="",
                    quantity=quantity,
                    unit=unit,
                    unit_price=unit_price,
                    total_price=0,  # Will be calculated
                    source_filename=plan.filename,
                    source_layer=f"PDF:{plan_type}",
                    confidence=item_confidence,
                    user_notes=user_note,
                    is_deleted=False,
                    is_modified=False,
                )

                # Calculate total price
                boq_item.total_price = boq_item.quantity * boq_item.unit_price

                db.add(boq_item)

            db.commit()
            logger.info(f"Created BOQ items from plan {plan.id}")

        except Exception as e:
            logger.error(f"Failed to process PDF plan {plan.id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # =========================================================================
    # Update cached totals for hierarchy
    # =========================================================================
    logger.info(f"Updating hierarchy totals for {len(created_sub_chapter_ids)} sub-chapters")
    for sub_chapter_id in created_sub_chapter_ids:
        update_hierarchy_totals(db, sub_chapter_id)

    db.commit()
    logger.info(f"PDF BOQ generation complete for project {project_id}")


def _estimate_price_with_ai(description: str, unit: str, quantity: float) -> tuple:
    """
    Use AI (Gemini) to estimate Israeli construction prices when Dekel pricing fails.

    Returns:
        tuple: (estimated_price, confidence, note)
        - estimated_price: float, the AI-estimated unit price in ILS
        - confidence: float, AI's confidence in the estimate (0.3-0.6)
        - note: str, explanation of the estimate
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from app.core.config import settings
        import os

        api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("No Gemini API key for price estimation")
            return (0, 0.3, "⚠️ אומדן AI לא זמין - נדרש תמחור ידני")

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1')
        )

        prompt = f"""אתה מומחה תמחור בנייה ישראלי. אנא העריך את המחיר ליחידה עבור הפריט הבא:

פריט: {description}
יחידת מידה: {unit}
כמות: {quantity}

הנחיות:
1. תן מחיר ליחידה אחת בש"ח (ILS) - מחיר סביר לשוק הישראלי 2024-2025
2. המחיר צריך לכלול: חומרים + עבודה + רווח קבלן (ללא מע"מ)
3. התבסס על מחירי שוק ריאליסטיים בישראל

החזר JSON בלבד בפורמט:
{{"unit_price": <מספר>, "confidence": <0.3-0.6>, "reasoning": "<הסבר קצר בעברית>"}}

דוגמאות מחירים לייחוס:
- חפירה כללית: 40-60 ₪/מ"ק
- בטון B30: 800-1200 ₪/מ"ק
- ריצוף קרמיקה: 150-300 ₪/מ"ר
- קיר בלוקים 20 ס"מ: 180-280 ₪/מ"ר
- צבע קירות: 25-45 ₪/מ"ר
- משטח גומי בטיחותי: 350-550 ₪/מ"ר"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=200,
            )
        )

        # Parse response
        import json
        import re

        text = response.text.strip()
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', text)
        if json_match:
            result = json.loads(json_match.group())
            price = float(result.get("unit_price", 0))
            conf = float(result.get("confidence", 0.4))
            reasoning = result.get("reasoning", "אומדן AI")

            if price > 0:
                note = f"💡 אומדן AI: {reasoning}"
                logger.info(f"AI estimated price for '{description[:30]}...': {price} ILS/unit (conf: {conf})")
                return (price, min(conf, 0.5), note)  # Cap confidence at 0.5 for estimates

        logger.warning(f"AI price estimation failed to parse for: {description[:40]}")
        return (0, 0.3, "⚠️ אומדן AI נכשל - נדרש תמחור ידני")

    except Exception as e:
        logger.error(f"AI price estimation error: {e}")
        return (0, 0.3, f"⚠️ שגיאת אומדן AI - נדרש תמחור ידני")


def _get_chapter_for_plan_type(plan_type: str) -> dict:
    """
    Map plan type to BOQ chapter according to מחירון דקל standard.

    Based on ISRAELI_BOQ_KNOWLEDGE_BASE.md - Appendix A:
    פרק 01 - עבודות הכנה, פירוק והריסה
    פרק 02 - עבודות עפר
    פרק 03 - בטון יצוק באתר
    פרק 04 - מבנים טרומיים
    פרק 05 - עבודות פלדה
    פרק 06 - עבודות בנייה
    פרק 07 - עבודות איטום
    פרק 08 - עבודות טיח
    פרק 09 - עבודות ריצוף וחיפוי
    פרק 10 - עבודות צבע
    פרק 11 - עבודות אלומיניום
    פרק 12 - מוצרי עץ ונגרות
    פרק 13 - עבודות מסגרות
    פרק 14 - עבודות אינסטלציה
    פרק 15 - עבודות חשמל
    פרק 16 - מערכות מיזוג אוויר
    פרק 17 - מעליות ומדרגות נעות
    פרק 18 - עבודות פיתוח ותשתית
    פרק 19 - עבודות גינון והשקייה
    פרק 20 - ציוד קבוע ואביזרים
    פרק 21 - עבודות שונות
    """
    plan_type_chapters = {
        # פרק 01 - עבודות הכנה, פירוק והריסה
        "demolition": {"code": "01", "name_he": "עבודות הכנה, פירוק והריסה", "name_en": "Preliminaries & Demolition"},
        "preliminary": {"code": "01", "name_he": "עבודות הכנה, פירוק והריסה", "name_en": "Preliminaries & Demolition"},

        # פרק 02 - עבודות עפר
        "earthworks": {"code": "02", "name_he": "עבודות עפר", "name_en": "Earthworks"},
        "excavation": {"code": "02", "name_he": "עבודות עפר", "name_en": "Earthworks"},

        # פרק 03 - בטון יצוק באתר
        "structural": {"code": "03", "name_he": "בטון יצוק באתר", "name_en": "Cast-in-place Concrete"},
        "concrete": {"code": "03", "name_he": "בטון יצוק באתר", "name_en": "Cast-in-place Concrete"},

        # פרק 04 - מבנים טרומיים
        "precast": {"code": "04", "name_he": "מבנים טרומיים", "name_en": "Precast Structures"},

        # פרק 05 - עבודות פלדה
        "steel": {"code": "05", "name_he": "עבודות פלדה", "name_en": "Steelwork"},

        # פרק 06 - עבודות בנייה
        "masonry": {"code": "06", "name_he": "עבודות בנייה", "name_en": "Masonry"},
        "architectural": {"code": "06", "name_he": "עבודות בנייה", "name_en": "Masonry"},

        # פרק 07 - עבודות איטום
        "waterproofing": {"code": "07", "name_he": "עבודות איטום", "name_en": "Waterproofing"},

        # פרק 08 - עבודות טיח
        "plastering": {"code": "08", "name_he": "עבודות טיח", "name_en": "Plastering"},

        # פרק 09 - עבודות ריצוף וחיפוי
        "flooring": {"code": "09", "name_he": "עבודות ריצוף וחיפוי", "name_en": "Flooring & Cladding"},
        "tiling": {"code": "09", "name_he": "עבודות ריצוף וחיפוי", "name_en": "Flooring & Cladding"},
        "finishing": {"code": "09", "name_he": "עבודות ריצוף וחיפוי", "name_en": "Flooring & Cladding"},

        # פרק 10 - עבודות צבע
        "painting": {"code": "10", "name_he": "עבודות צבע", "name_en": "Painting"},

        # פרק 11 - עבודות אלומיניום
        "aluminum": {"code": "11", "name_he": "עבודות אלומיניום", "name_en": "Aluminum Works"},
        "windows_doors": {"code": "11", "name_he": "עבודות אלומיניום", "name_en": "Aluminum Works"},

        # פרק 12 - מוצרי עץ ונגרות
        "carpentry": {"code": "12", "name_he": "מוצרי עץ ונגרות", "name_en": "Carpentry"},
        "wood": {"code": "12", "name_he": "מוצרי עץ ונגרות", "name_en": "Carpentry"},

        # פרק 13 - עבודות מסגרות
        "metalwork": {"code": "13", "name_he": "עבודות מסגרות", "name_en": "Metalwork"},

        # פרק 14 - עבודות אינסטלציה
        "plumbing": {"code": "14", "name_he": "עבודות אינסטלציה", "name_en": "Plumbing"},

        # פרק 15 - עבודות חשמל
        "electrical": {"code": "15", "name_he": "עבודות חשמל", "name_en": "Electrical"},

        # פרק 16 - מערכות מיזוג אוויר
        "hvac": {"code": "16", "name_he": "מערכות מיזוג אוויר", "name_en": "HVAC"},

        # פרק 17 - מעליות ומדרגות נעות
        "elevators": {"code": "17", "name_he": "מעליות ומדרגות נעות", "name_en": "Elevators"},

        # פרק 18 - עבודות פיתוח ותשתית
        "site_development": {"code": "18", "name_he": "עבודות פיתוח ותשתית", "name_en": "Site Development"},

        # פרק 19 - עבודות גינון והשקייה
        "landscape": {"code": "19", "name_he": "עבודות גינון והשקייה", "name_en": "Landscaping"},

        # פרק 20 - ציוד קבוע ואביזרים
        "equipment": {"code": "20", "name_he": "ציוד קבוע ואביזרים", "name_en": "Fixed Equipment"},

        # פרק 21 - עבודות שונות
        "general": {"code": "21", "name_he": "עבודות שונות", "name_en": "Miscellaneous"},
        "boq_table": {"code": "21", "name_he": "עבודות שונות", "name_en": "Miscellaneous"},
    }
    return plan_type_chapters.get(plan_type, plan_type_chapters["general"])


def _categorize_item_to_subchapter(description: str, chapter_code: str) -> tuple:
    """
    Categorize BOQ item to sub-chapter and section based on description.
    Returns (sub_chapter, section) tuple for 4-level code structure.

    Professional Israeli BOQ structure: פרק.תת_פרק.סעיף.מספר
    Example: 3.1.1.0010 = Chapter 3, Sub-chapter 1, Section 1, Item 10

    This is GENERIC - works for any project type.
    """
    desc_lower = description.lower()

    # Site Development (פרק 13) - פיתוח
    if chapter_code == "13":
        # Sub-chapter 1: חפירה ודיפון (Excavation & Shoring)
        if any(word in desc_lower for word in ["חפירה", "דיפון", "חפר", "excavation", "shoring"]):
            return ("1", "1")
        # Sub-chapter 2: קירות תמך ויסודות (Retaining Walls & Foundations)
        if any(word in desc_lower for word in ["קיר תמך", "קירות תמך", "יסוד", "retaining", "foundation"]):
            return ("1", "2")
        # Sub-chapter 3: ניקוז ותיעול (Drainage)
        if any(word in desc_lower for word in ["ניקוז", "תיעול", "תעלה", "drainage", "channel"]):
            return ("2", "1")
        # Sub-chapter 4: ריצוף ומשטחים (Paving & Surfaces)
        if any(word in desc_lower for word in ["ריצוף", "מרצפ", "משטח", "אספלט", "paving", "surface", "asphalt"]):
            return ("3", "1")
        # Sub-chapter 5: גינון (Landscaping)
        if any(word in desc_lower for word in ["גינון", "דשא", "עץ", "שיח", "צמח", "landscap", "grass", "tree", "plant"]):
            return ("4", "1")
        # Sub-chapter 6: גדרות ומעקות (Fences & Railings)
        if any(word in desc_lower for word in ["גדר", "מעקה", "fence", "railing"]):
            return ("5", "1")
        # Sub-chapter 7: ציוד חוץ (Outdoor Equipment)
        if any(word in desc_lower for word in ["ספסל", "פח אשפה", "מתקן", "bench", "equipment"]):
            return ("6", "1")
        # Default for site development
        return ("9", "1")

    # Earthworks (פרק 01) - עבודות עפר
    if chapter_code == "01":
        if any(word in desc_lower for word in ["חפירה", "חפר", "excavat"]):
            return ("1", "1")
        if any(word in desc_lower for word in ["מילוי", "הידוק", "fill", "compact"]):
            return ("2", "1")
        if any(word in desc_lower for word in ["פינוי", "הובלה", "remov", "transport"]):
            return ("3", "1")
        return ("1", "1")

    # Concrete (פרק 02) - עבודות בטון
    if chapter_code == "02":
        if any(word in desc_lower for word in ["יסוד", "רצועה", "foundation", "strip"]):
            return ("1", "1")
        if any(word in desc_lower for word in ["עמוד", "column"]):
            return ("2", "1")
        if any(word in desc_lower for word in ["קורה", "beam"]):
            return ("3", "1")
        if any(word in desc_lower for word in ["תקרה", "רצפה", "slab", "floor"]):
            return ("4", "1")
        if any(word in desc_lower for word in ["קיר", "wall"]):
            return ("5", "1")
        return ("1", "1")

    # Masonry (פרק 04) - בנייה
    if chapter_code == "04":
        if any(word in desc_lower for word in ["בלוק", "block"]):
            return ("1", "1")
        if any(word in desc_lower for word in ["לבנ", "brick"]):
            return ("2", "1")
        return ("1", "1")

    # Electrical (פרק 05) - חשמל
    if chapter_code == "05":
        if any(word in desc_lower for word in ["תאורה", "נורה", "light"]):
            return ("1", "1")
        if any(word in desc_lower for word in ["שקע", "outlet", "socket"]):
            return ("2", "1")
        if any(word in desc_lower for word in ["לוח", "panel", "board"]):
            return ("3", "1")
        return ("1", "1")

    # Plumbing (פרק 07) - אינסטלציה
    if chapter_code == "07":
        if any(word in desc_lower for word in ["מים קרים", "cold water"]):
            return ("1", "1")
        if any(word in desc_lower for word in ["מים חמים", "hot water"]):
            return ("1", "2")
        if any(word in desc_lower for word in ["ביוב", "sewage"]):
            return ("2", "1")
        if any(word in desc_lower for word in ["כלי סניטר", "sanitary"]):
            return ("3", "1")
        return ("1", "1")

    # Traffic Works (פרק 14) - עבודות תנועה
    if chapter_code == "14":
        # Sub-chapter 1: סימון אופקי (Horizontal Road Markings)
        if any(word in desc_lower for word in [
            "סימון", "marking", "קו", "line", "פס", "stripe",
            "חץ", "arrow", "מעבר חציה", "zebra", "crosswalk"
        ]):
            return ("1", "1")
        # Sub-chapter 2: תמרורים ושילוט (Signs & Signage)
        if any(word in desc_lower for word in [
            "תמרור", "sign", "שלט", "signage", "עמוד שילוט"
        ]):
            return ("2", "1")
        # Sub-chapter 3: מעקות בטיחות (Safety Barriers/Guardrails)
        if any(word in desc_lower for word in [
            "מעקה", "guardrail", "barrier", "w-beam", "גל", "בטיחות"
        ]):
            return ("3", "1")
        # Sub-chapter 4: פסי האטה ובליטות (Speed Control)
        if any(word in desc_lower for word in [
            "פס האטה", "speed bump", "האטה", "blitta", "בליטה",
            "speed cushion", "הרגעת תנועה", "traffic calm"
        ]):
            return ("4", "1")
        # Sub-chapter 5: תאורת רחוב (Street Lighting)
        if any(word in desc_lower for word in [
            "תאורה", "lighting", "עמוד תאורה", "פנס", "lamp", "led",
            "נורה", "מנורה", "street light"
        ]):
            return ("5", "1")
        # Sub-chapter 6: איי תנועה (Traffic Islands)
        if any(word in desc_lower for word in [
            "אי תנועה", "traffic island", "איים", "island", "כיכר",
            "roundabout", "מפריד", "separator", "refuge"
        ]):
            return ("6", "1")
        # Sub-chapter 7: חניות (Parking)
        if any(word in desc_lower for word in [
            "חניה", "parking", "חנייה", "מגרש חניה", "lot",
            "מחסום חניה", "parking barrier"
        ]):
            return ("7", "1")
        # Sub-chapter 8: מדרכות ושבילים (Sidewalks & Paths)
        if any(word in desc_lower for word in [
            "מדרכה", "sidewalk", "שביל", "path", "אופניים", "bicycle",
            "רוכב", "אבני שפה", "curb", "kerb"
        ]):
            return ("8", "1")
        # Sub-chapter 9: ניקוז כבישים (Road Drainage)
        if any(word in desc_lower for word in [
            "ניקוז", "drainage", "תעלה", "channel", "גשם", "rain",
            "תא ניקוז", "catch basin", "סכר"
        ]):
            return ("9", "1")
        # Default for traffic works
        return ("1", "1")

    # Default - use generic structure
    return ("1", "1")


def _generate_hierarchical_item_code(
    chapter_code: str,
    sub_chapter: str,
    section: str,
    item_num: int
) -> str:
    """
    Generate professional 4-level Israeli BOQ item code.

    Format: פרק.תת_פרק.סעיף.מספר
    Example: 3.1.1.0010

    This matches the structure used in professional Israeli BOQs
    and Dekel pricing system.
    """
    # Remove leading zeros from chapter for cleaner format
    chapter = chapter_code.lstrip('0') or '0'

    # Format: X.Y.Z.NNNN (4-digit item number for sorting)
    return f"{chapter}.{sub_chapter}.{section}.{item_num:04d}"


def _get_sub_chapter_name(chapter_code: str, sub_chapter_code: str) -> str:
    """
    Get Hebrew name for sub-chapter based on chapter and sub-chapter codes.
    Returns the professional Israeli BOQ sub-chapter name.
    """
    # Sub-chapter names by chapter
    SUB_CHAPTER_NAMES = {
        # פרק 13 - עבודות פיתוח
        "13": {
            "1": "חפירה ודיפון",
            "2": "ניקוז ותיעול",
            "3": "ריצוף ומשטחים",
            "4": "גינון ונטיעות",
            "5": "גדרות ומעקות",
            "6": "ציוד חוץ",
            "9": "עבודות שונות",
        },
        # פרק 01 - עבודות עפר
        "01": {
            "1": "חפירה",
            "2": "מילוי והידוק",
            "3": "פינוי והובלה",
        },
        # פרק 02 - עבודות בטון
        "02": {
            "1": "יסודות",
            "2": "עמודים",
            "3": "קורות",
            "4": "תקרות ורצפות",
            "5": "קירות",
        },
        # פרק 05 - עבודות חשמל
        "05": {
            "1": "תאורה",
            "2": "שקעים",
            "3": "לוחות חשמל",
        },
        # פרק 14 - עבודות תנועה
        "14": {
            "1": "סימון אופקי",
            "2": "תמרורים ושילוט",
            "3": "מעקות בטיחות",
            "4": "פסי האטה",
            "5": "תאורת רחוב",
            "6": "איי תנועה",
            "7": "חניות",
        },
    }

    chapter_names = SUB_CHAPTER_NAMES.get(chapter_code, SUB_CHAPTER_NAMES.get(chapter_code.lstrip('0'), {}))
    return chapter_names.get(sub_chapter_code, f"תת פרק {sub_chapter_code}")


def _get_item_description(item: dict) -> str:
    """Get description for BOQ item from extracted data."""
    # Try various fields for description
    desc = item.get("description", "")
    if desc:
        return str(desc)

    name = item.get("name", "")
    item_type = item.get("type", "")

    if name and item_type:
        return f"{item_type}: {name}"
    elif name:
        return str(name)
    elif item_type:
        return str(item_type)

    # Build description from available fields
    parts = []
    for key in ["material", "size", "specs", "location"]:
        if item.get(key):
            parts.append(str(item[key]))

    return " - ".join(parts) if parts else "פריט מחילוץ PDF"


def _get_item_quantity(item: dict) -> float:
    """Get quantity from extracted item."""
    # Try various quantity fields
    for key in ["quantity", "area_m2", "count", "length_m", "amount"]:
        val = item.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    return 1.0


def _detect_pdf_plan_type(filename: str) -> str:
    """
    Auto-detect plan type from PDF filename using Hebrew/English keywords.

    Returns one of the plan types:
    - boq_table: כתב כמויות (BOQ document)
    - architectural: תכנית אדריכלית
    - electrical: תכנית חשמל
    - plumbing: תכנית אינסטלציה
    - structural: תכנית קונסטרוקציה
    - hvac: תכנית מיזוג אוויר
    - windows_doors: לוח חלונות ודלתות
    - finishing: תכנית גמרים
    - landscape: תכנית גינון
    - site_development: תכנית פיתוח
    - general: default
    """
    filename_lower = filename.lower()

    # Hebrew and English keyword patterns for each type
    patterns = {
        "boq_table": [
            "כתב כמויות", "כמויות", "boq", "כ\"כ", "כ.כ", "כ\"כ",
            "bill of quantities", "quantity", "מפרט"
        ],
        "traffic": [
            "תנועה", "תמרור", "traffic", "signage", "סימון", "marking",
            "כביש", "road", "חניה", "parking", "מעבר חציה", "crosswalk",
            "מדרכה", "sidewalk", "תאורת רחוב", "street light", "מעקה בטיחות",
            "guardrail", "פס האטה", "speed bump", "אי תנועה", "traffic island"
        ],
        "site_development": [
            "פיתוח", "פתוח", "site", "development", "גינון ופיתוח",
            "עבודות חוץ", "שטח", "חצר"
        ],
        "electrical": [
            "חשמל", "electric", "elec", "תאורה", "lighting", "מתח"
        ],
        "plumbing": [
            "אינסטלציה", "סניטרי", "plumb", "sanit", "ביוב", "מים", "צנרת"
        ],
        "structural": [
            "קונסטרוקציה", "מבנה", "struct", "בטון", "יסודות", "עמודים"
        ],
        "hvac": [
            "מיזוג", "hvac", "אוויר", "air condition", "מזגן", "ventil"
        ],
        "windows_doors": [
            "חלונות", "דלתות", "אלומ", "window", "door", "לוח חלונות"
        ],
        "finishing": [
            "גמר", "גמרים", "finish", "ריצוף", "חיפוי", "צבע", "טיח"
        ],
        "landscape": [
            "גינון", "נוף", "landscape", "garden", "צמחיה", "דשא"
        ],
        "architectural": [
            "אדריכל", "בניה", "arch", "תכנית", "קומה", "חזית", "חתך"
        ],
    }

    # Check each pattern type
    for plan_type, keywords in patterns.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return plan_type

    return "general"


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
    # If at drive root (e.g., C:\), parent_path = "" to go back to drive list
    # Otherwise, get the actual parent folder
    if folder.parent == folder:
        # We're at a drive root (C:\, D:\, etc.) - go back to drive list
        parent_path = ""
    else:
        parent_path = str(folder.parent)

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
    Delete a project and all its plans from the database.
    Note: Original files in the folder are NOT deleted - only database records.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count plans for response
    plan_count = len(project.plans)

    # Delete from database only (cascade will delete plans, materials, BOQ items)
    # Original files in the folder are preserved
    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully",
        "id": project_id,
        "deleted_plans": plan_count,
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

    # Start background processing (creates its own session)
    background_tasks.add_task(process_project_files, project_id)

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
        # Return empty BOQ structure instead of error for better UX
        return {
            "project_name": project.name,
            "project_id": project.id,
            "date": datetime.now().isoformat(),
            "chapters": [],
            "summary": {
                "subtotal": 0,
                "vat_rate": 0.17,
                "vat_amount": 0,
                "grand_total": 0,
                "total_files": len(project.plans),
                "total_items": 0
            },
            "source_files": [],
            "notes": [],
            "warning": "No BOQ data available. Process files to generate BOQ."
        }

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

                # Check if this is a PDF extraction (has different fields)
                is_pdf = data.get("extraction_method", "").startswith("vision_ai")

                if is_pdf:
                    # PDF extraction data
                    total_text += data.get("items_count", 0)  # Count items as "text"
                    # PDF area is already in m²
                    area_m2 = data.get("total_area_m2", 0)
                    plan_extraction["area_m2"] = round(area_m2, 2)
                    total_area_m2 += area_m2
                    # Count extracted items
                    items = data.get("extracted_items", [])
                    plan_extraction["items_count"] = len(items)
                else:
                    # CAD extraction data
                    total_blocks += data.get("blocks_count", 0)
                    total_text += data.get("text_count", 0)
                    total_layers += data.get("layers_count", 0)
                    total_polylines += data.get("polylines_count", 0)

                    # CAD area: check if already converted to m² or still in raw units
                    if "total_area_m2" in data:
                        area_m2 = data.get("total_area_m2", 0)
                    else:
                        # Legacy: convert from cm² to m²
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

    For PDF-only projects (no CAD layers), BOQ is generated directly from PDF extraction data.
    """
    import logging
    logger = logging.getLogger(__name__)

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    selected_layer_ids = set(selection.selected_layer_ids) if selection.selected_layer_ids else set()
    custom_area = selection.custom_area_m2

    # Check if this is a PDF-only project (no CAD files)
    pdf_plans = []
    has_cad_files = False

    for plan in project.plans:
        file_ext = os.path.splitext(plan.filename)[1].lower()
        if file_ext == '.pdf':
            pdf_plans.append(plan)
        elif file_ext in {'.dwg', '.dxf'}:
            has_cad_files = True

    # PDF-only project - generate BOQ directly from PDF extractions
    if not has_cad_files and pdf_plans:
        logger.info(f"PDF-only project {project_id} - generating BOQ directly from PDF data")
        project.processing_status = "generating_boq"
        db.commit()

        try:
            _generate_boq_from_pdf_extractions(project_id, pdf_plans, db)
            project.processing_status = "completed"
            project.processing_progress = 100
            db.commit()
            logger.info(f"PDF BOQ generation completed for project {project_id}")

            return {
                "message": "PDF BOQ generation completed",
                "project_id": project_id,
                "selected_layer_ids": [],
                "selected_layer_names": [],
                "selected_area_m2": 0,
                "final_area_m2": 0,
                "custom_override": False,
                "status": "completed",
                "is_pdf_only": True
            }
        except Exception as e:
            logger.error(f"PDF BOQ generation failed: {e}")
            project.processing_status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=f"PDF BOQ generation failed: {str(e)}")

    # CAD files present - use layer selection workflow
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


