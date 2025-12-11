"""
BOQ Hierarchy API Endpoints
===========================

Provides full 4-level hierarchical BOQ management:
- תת כתב (Sub-Document) - Level 1
- פרק (Chapter) - Level 2
- תת פרק (Sub-Chapter) - Level 3
- סעיף (Item) - Level 4

Generic implementation supporting any project type.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import logging

from app.api import deps
from app import models, schemas

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Full Hierarchical BOQ Endpoint
# =============================================================================

@router.get("/{project_id}/boq/hierarchy", response_model=schemas.BOQHierarchyResponse)
def get_boq_hierarchy(
    project_id: int,
    include_deleted: bool = False,
    db: Session = Depends(deps.get_db)
):
    """
    Get full 4-level hierarchical BOQ for a project.

    Returns nested structure:
    - Sub-Documents (תת כתב)
      - Chapters (פרק)
        - Sub-Chapters (תת פרק)
          - Items (סעיף)

    Each level includes cached totals for performance.
    """
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build hierarchical response using helper from schemas
    return schemas.build_hierarchy_response(db, project_id, include_deleted)


@router.get("/{project_id}/boq/hierarchy/summary", response_model=schemas.BOQHierarchySummary)
def get_boq_hierarchy_summary(
    project_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get summary statistics for the hierarchical BOQ.

    Returns counts and totals at each level.
    """
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count at each level
    sub_doc_count = db.query(func.count(models.BOQSubDocument.id)).filter(
        models.BOQSubDocument.project_id == project_id
    ).scalar() or 0

    chapter_count = db.query(func.count(models.BOQChapter.id)).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubDocument.project_id == project_id
    ).scalar() or 0

    sub_chapter_count = db.query(func.count(models.BOQSubChapter.id)).join(
        models.BOQChapter
    ).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubDocument.project_id == project_id
    ).scalar() or 0

    item_count = db.query(func.count(models.BOQItem.id)).filter(
        models.BOQItem.project_id == project_id,
        models.BOQItem.is_deleted == False
    ).scalar() or 0

    # Get grand total
    grand_total = db.query(func.sum(models.BOQItem.total_price)).filter(
        models.BOQItem.project_id == project_id,
        models.BOQItem.is_deleted == False
    ).scalar() or 0.0

    return {
        "project_id": project_id,
        "sub_document_count": sub_doc_count,
        "chapter_count": chapter_count,
        "sub_chapter_count": sub_chapter_count,
        "item_count": item_count,
        "grand_total": grand_total
    }


# =============================================================================
# Sub-Document (תת כתב) CRUD - Level 1
# =============================================================================

@router.get("/{project_id}/boq/sub-documents", response_model=List[schemas.BOQSubDocumentSummary])
def list_sub_documents(
    project_id: int,
    db: Session = Depends(deps.get_db)
):
    """List all sub-documents for a project with chapter counts and totals."""
    sub_docs = db.query(models.BOQSubDocument).filter(
        models.BOQSubDocument.project_id == project_id
    ).order_by(models.BOQSubDocument.display_order).all()

    result = []
    for sd in sub_docs:
        chapter_count = len(sd.chapters) if sd.chapters else 0
        result.append({
            "id": sd.id,
            "code": sd.code,
            "name_he": sd.name_he,
            "name_en": sd.name_en,
            "display_order": sd.display_order,
            "cached_total": sd.cached_total or 0,
            "chapter_count": chapter_count
        })

    return result


@router.post("/{project_id}/boq/sub-documents", response_model=schemas.BOQSubDocumentSummary)
def create_sub_document(
    project_id: int,
    data: schemas.BOQSubDocumentCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new sub-document (תת כתב)."""
    # Verify project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check for duplicate code
    existing = db.query(models.BOQSubDocument).filter(
        models.BOQSubDocument.project_id == project_id,
        models.BOQSubDocument.code == data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Sub-document with code '{data.code}' already exists")

    sub_doc = models.BOQSubDocument(
        project_id=project_id,
        code=data.code,
        name_he=data.name_he,
        name_en=data.name_en,
        display_order=data.display_order or 0,
        description=data.description
    )

    db.add(sub_doc)
    db.commit()
    db.refresh(sub_doc)

    return {
        "id": sub_doc.id,
        "code": sub_doc.code,
        "name_he": sub_doc.name_he,
        "name_en": sub_doc.name_en,
        "display_order": sub_doc.display_order,
        "cached_total": 0,
        "chapter_count": 0
    }


@router.patch("/{project_id}/boq/sub-documents/{sub_doc_id}")
def update_sub_document(
    project_id: int,
    sub_doc_id: int,
    data: schemas.BOQSubDocumentUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update a sub-document."""
    sub_doc = db.query(models.BOQSubDocument).filter(
        models.BOQSubDocument.id == sub_doc_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not sub_doc:
        raise HTTPException(status_code=404, detail="Sub-document not found")

    if data.code is not None:
        sub_doc.code = data.code
    if data.name_he is not None:
        sub_doc.name_he = data.name_he
    if data.name_en is not None:
        sub_doc.name_en = data.name_en
    if data.display_order is not None:
        sub_doc.display_order = data.display_order
    if data.description is not None:
        sub_doc.description = data.description

    db.commit()
    db.refresh(sub_doc)

    return {"message": "Sub-document updated", "id": sub_doc.id}


@router.delete("/{project_id}/boq/sub-documents/{sub_doc_id}")
def delete_sub_document(
    project_id: int,
    sub_doc_id: int,
    db: Session = Depends(deps.get_db)
):
    """Delete a sub-document and all its children (cascade)."""
    sub_doc = db.query(models.BOQSubDocument).filter(
        models.BOQSubDocument.id == sub_doc_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not sub_doc:
        raise HTTPException(status_code=404, detail="Sub-document not found")

    db.delete(sub_doc)
    db.commit()

    return {"message": "Sub-document deleted"}


# =============================================================================
# Chapter (פרק) CRUD - Level 2
# =============================================================================

@router.get("/{project_id}/boq/sub-documents/{sub_doc_id}/chapters",
            response_model=List[schemas.BOQChapterSummary])
def list_chapters(
    project_id: int,
    sub_doc_id: int,
    db: Session = Depends(deps.get_db)
):
    """List all chapters in a sub-document."""
    chapters = db.query(models.BOQChapter).filter(
        models.BOQChapter.sub_document_id == sub_doc_id
    ).order_by(models.BOQChapter.display_order).all()

    result = []
    for ch in chapters:
        sub_chapter_count = len(ch.sub_chapters) if ch.sub_chapters else 0
        result.append({
            "id": ch.id,
            "code": ch.code,
            "name_he": ch.name_he,
            "name_en": ch.name_en,
            "dekel_code": ch.dekel_code,
            "display_order": ch.display_order,
            "cached_total": ch.cached_total or 0,
            "sub_chapter_count": sub_chapter_count
        })

    return result


@router.post("/{project_id}/boq/sub-documents/{sub_doc_id}/chapters",
             response_model=schemas.BOQChapterSummary)
def create_chapter(
    project_id: int,
    sub_doc_id: int,
    data: schemas.BOQChapterCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new chapter (פרק) in a sub-document."""
    # Verify sub-document exists and belongs to project
    sub_doc = db.query(models.BOQSubDocument).filter(
        models.BOQSubDocument.id == sub_doc_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not sub_doc:
        raise HTTPException(status_code=404, detail="Sub-document not found")

    chapter = models.BOQChapter(
        sub_document_id=sub_doc_id,
        code=data.code,
        name_he=data.name_he,
        name_en=data.name_en,
        dekel_code=data.dekel_code,
        display_order=data.display_order or 0,
        description=data.description
    )

    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    return {
        "id": chapter.id,
        "code": chapter.code,
        "name_he": chapter.name_he,
        "name_en": chapter.name_en,
        "dekel_code": chapter.dekel_code,
        "display_order": chapter.display_order,
        "cached_total": 0,
        "sub_chapter_count": 0
    }


@router.patch("/{project_id}/boq/chapters/{chapter_id}")
def update_chapter(
    project_id: int,
    chapter_id: int,
    data: schemas.BOQChapterUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update a chapter."""
    chapter = db.query(models.BOQChapter).join(
        models.BOQSubDocument
    ).filter(
        models.BOQChapter.id == chapter_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if data.code is not None:
        chapter.code = data.code
    if data.name_he is not None:
        chapter.name_he = data.name_he
    if data.name_en is not None:
        chapter.name_en = data.name_en
    if data.dekel_code is not None:
        chapter.dekel_code = data.dekel_code
    if data.display_order is not None:
        chapter.display_order = data.display_order
    if data.description is not None:
        chapter.description = data.description

    db.commit()
    db.refresh(chapter)

    return {"message": "Chapter updated", "id": chapter.id}


@router.delete("/{project_id}/boq/chapters/{chapter_id}")
def delete_chapter(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(deps.get_db)
):
    """Delete a chapter and all its sub-chapters (cascade)."""
    chapter = db.query(models.BOQChapter).join(
        models.BOQSubDocument
    ).filter(
        models.BOQChapter.id == chapter_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    db.delete(chapter)
    db.commit()

    return {"message": "Chapter deleted"}


# =============================================================================
# Sub-Chapter (תת פרק) CRUD - Level 3
# =============================================================================

@router.get("/{project_id}/boq/chapters/{chapter_id}/sub-chapters",
            response_model=List[schemas.BOQSubChapterSummary])
def list_sub_chapters(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(deps.get_db)
):
    """List all sub-chapters in a chapter."""
    sub_chapters = db.query(models.BOQSubChapter).filter(
        models.BOQSubChapter.chapter_id == chapter_id
    ).order_by(models.BOQSubChapter.display_order).all()

    result = []
    for sc in sub_chapters:
        item_count = len(sc.items) if sc.items else 0
        result.append({
            "id": sc.id,
            "code": sc.code,
            "name_he": sc.name_he,
            "name_en": sc.name_en,
            "display_order": sc.display_order,
            "cached_total": sc.cached_total or 0,
            "item_count": item_count
        })

    return result


@router.post("/{project_id}/boq/chapters/{chapter_id}/sub-chapters",
             response_model=schemas.BOQSubChapterSummary)
def create_sub_chapter(
    project_id: int,
    chapter_id: int,
    data: schemas.BOQSubChapterCreate,
    db: Session = Depends(deps.get_db)
):
    """Create a new sub-chapter (תת פרק) in a chapter."""
    # Verify chapter exists and belongs to project
    chapter = db.query(models.BOQChapter).join(
        models.BOQSubDocument
    ).filter(
        models.BOQChapter.id == chapter_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    sub_chapter = models.BOQSubChapter(
        chapter_id=chapter_id,
        code=data.code,
        name_he=data.name_he,
        name_en=data.name_en,
        display_order=data.display_order or 0,
        description=data.description
    )

    db.add(sub_chapter)
    db.commit()
    db.refresh(sub_chapter)

    return {
        "id": sub_chapter.id,
        "code": sub_chapter.code,
        "name_he": sub_chapter.name_he,
        "name_en": sub_chapter.name_en,
        "display_order": sub_chapter.display_order,
        "cached_total": 0,
        "item_count": 0
    }


@router.patch("/{project_id}/boq/sub-chapters/{sub_chapter_id}")
def update_sub_chapter(
    project_id: int,
    sub_chapter_id: int,
    data: schemas.BOQSubChapterUpdate,
    db: Session = Depends(deps.get_db)
):
    """Update a sub-chapter."""
    sub_chapter = db.query(models.BOQSubChapter).join(
        models.BOQChapter
    ).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubChapter.id == sub_chapter_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not sub_chapter:
        raise HTTPException(status_code=404, detail="Sub-chapter not found")

    if data.code is not None:
        sub_chapter.code = data.code
    if data.name_he is not None:
        sub_chapter.name_he = data.name_he
    if data.name_en is not None:
        sub_chapter.name_en = data.name_en
    if data.display_order is not None:
        sub_chapter.display_order = data.display_order
    if data.description is not None:
        sub_chapter.description = data.description

    db.commit()
    db.refresh(sub_chapter)

    return {"message": "Sub-chapter updated", "id": sub_chapter.id}


@router.delete("/{project_id}/boq/sub-chapters/{sub_chapter_id}")
def delete_sub_chapter(
    project_id: int,
    sub_chapter_id: int,
    db: Session = Depends(deps.get_db)
):
    """Delete a sub-chapter. Items will have sub_chapter_id set to NULL."""
    sub_chapter = db.query(models.BOQSubChapter).join(
        models.BOQChapter
    ).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubChapter.id == sub_chapter_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not sub_chapter:
        raise HTTPException(status_code=404, detail="Sub-chapter not found")

    db.delete(sub_chapter)
    db.commit()

    return {"message": "Sub-chapter deleted"}


# =============================================================================
# Hierarchy Management
# =============================================================================

@router.post("/{project_id}/boq/hierarchy/recalculate")
def recalculate_hierarchy_totals(
    project_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Recalculate cached totals at all hierarchy levels.

    Call this after bulk item updates or imports.
    """
    # Get all sub-chapters for the project
    sub_chapters = db.query(models.BOQSubChapter).join(
        models.BOQChapter
    ).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubDocument.project_id == project_id
    ).all()

    # Recalculate each sub-chapter
    for sc in sub_chapters:
        models.update_hierarchy_totals(db, sc.id)

    db.commit()

    return {"message": f"Recalculated totals for {len(sub_chapters)} sub-chapters"}


@router.post("/{project_id}/boq/hierarchy/assign-item")
def assign_item_to_hierarchy(
    project_id: int,
    item_id: int = Query(..., description="BOQ item ID"),
    sub_chapter_id: int = Query(..., description="Target sub-chapter ID"),
    section_code: Optional[str] = Query(None, description="Section code within sub-chapter"),
    db: Session = Depends(deps.get_db)
):
    """
    Assign a BOQ item to a sub-chapter in the hierarchy.

    This links a legacy flat item to the 4-level hierarchy.
    """
    # Get item
    item = db.query(models.BOQItem).filter(
        models.BOQItem.id == item_id,
        models.BOQItem.project_id == project_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="BOQ item not found")

    # Verify sub-chapter belongs to project
    sub_chapter = db.query(models.BOQSubChapter).join(
        models.BOQChapter
    ).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubChapter.id == sub_chapter_id,
        models.BOQSubDocument.project_id == project_id
    ).first()

    if not sub_chapter:
        raise HTTPException(status_code=404, detail="Sub-chapter not found")

    # Assign item
    item.sub_chapter_id = sub_chapter_id
    if section_code:
        item.section_code = section_code

    # Generate full item code
    item.full_item_code = item.compute_full_code()

    db.commit()

    # Update totals
    models.update_hierarchy_totals(db, sub_chapter_id)
    db.commit()

    return {
        "message": "Item assigned to hierarchy",
        "item_id": item_id,
        "full_code": item.full_item_code
    }


@router.post("/{project_id}/boq/hierarchy/bulk-assign")
def bulk_assign_items_to_hierarchy(
    project_id: int,
    assignments: List[Dict[str, Any]],
    db: Session = Depends(deps.get_db)
):
    """
    Bulk assign multiple items to the hierarchy.

    Request body should be a list of:
    [
        {"item_id": 1, "sub_chapter_id": 10, "section_code": "0010"},
        {"item_id": 2, "sub_chapter_id": 10, "section_code": "0020"},
        ...
    ]
    """
    success_count = 0
    error_count = 0
    affected_sub_chapters = set()

    for assignment in assignments:
        item_id = assignment.get("item_id")
        sub_chapter_id = assignment.get("sub_chapter_id")
        section_code = assignment.get("section_code")

        if not item_id or not sub_chapter_id:
            error_count += 1
            continue

        try:
            item = db.query(models.BOQItem).filter(
                models.BOQItem.id == item_id,
                models.BOQItem.project_id == project_id
            ).first()

            if item:
                item.sub_chapter_id = sub_chapter_id
                item.section_code = section_code
                item.full_item_code = item.compute_full_code()
                affected_sub_chapters.add(sub_chapter_id)
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            logger.error(f"Error assigning item {item_id}: {e}")
            error_count += 1

    db.commit()

    # Update totals for affected sub-chapters
    for sc_id in affected_sub_chapters:
        models.update_hierarchy_totals(db, sc_id)

    db.commit()

    return {
        "message": "Bulk assignment complete",
        "success": success_count,
        "errors": error_count,
        "sub_chapters_updated": len(affected_sub_chapters)
    }


@router.post("/{project_id}/boq/hierarchy/auto-organize")
def auto_organize_legacy_items(
    project_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Automatically organize legacy flat BOQ items into the hierarchy.

    Uses chapter_code and item_code patterns to create hierarchy:
    - Parses item codes like "01.001.0010" into sub_doc.chapter.sub_chapter.section
    - Creates missing hierarchy levels
    - Assigns items to appropriate sub-chapters
    """
    # Get legacy items (those without sub_chapter_id)
    legacy_items = db.query(models.BOQItem).filter(
        models.BOQItem.project_id == project_id,
        models.BOQItem.sub_chapter_id == None,
        models.BOQItem.is_deleted == False
    ).all()

    if not legacy_items:
        return {"message": "No legacy items to organize", "organized": 0}

    organized_count = 0

    for item in legacy_items:
        # Parse item code
        item_code = item.item_code or ""
        parsed = models.parse_item_code(item_code)

        if not parsed:
            # Try to use chapter_code if item_code parsing fails
            if item.chapter_code:
                parsed = {
                    "sub_doc_code": "1",
                    "chapter_code": item.chapter_code,
                    "sub_chapter_code": "1",
                    "section_code": item_code.split(".")[-1] if "." in item_code else "0010"
                }
            else:
                continue

        try:
            # Get or create sub-document
            sub_doc = models.get_or_create_sub_document(
                db, project_id,
                code=parsed["sub_doc_code"],
                name_he=f"תת כתב {parsed['sub_doc_code']}"
            )

            # Get or create chapter
            chapter_name = item.chapter_name_he or f"פרק {parsed['chapter_code']}"
            chapter = models.get_or_create_chapter(
                db, sub_doc.id,
                code=parsed["chapter_code"],
                name_he=chapter_name
            )

            # Get or create sub-chapter
            sub_chapter = models.get_or_create_sub_chapter(
                db, chapter.id,
                code=parsed["sub_chapter_code"],
                name_he=f"תת פרק {parsed['sub_chapter_code']}"
            )

            # Assign item
            item.sub_chapter_id = sub_chapter.id
            item.section_code = parsed["section_code"]
            item.full_item_code = item.compute_full_code()

            organized_count += 1

        except Exception as e:
            logger.error(f"Error organizing item {item.id}: {e}")
            continue

    db.commit()

    # Recalculate all totals
    sub_chapters = db.query(models.BOQSubChapter).join(
        models.BOQChapter
    ).join(
        models.BOQSubDocument
    ).filter(
        models.BOQSubDocument.project_id == project_id
    ).all()

    for sc in sub_chapters:
        models.update_hierarchy_totals(db, sc.id)

    db.commit()

    return {
        "message": "Legacy items organized into hierarchy",
        "organized": organized_count,
        "total_legacy": len(legacy_items)
    }
