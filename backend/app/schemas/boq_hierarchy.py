"""
Pydantic Schemas for Hierarchical BOQ Structure
================================================

Implements schemas for the 4-level Israeli BOQ hierarchy:
1. תת כתב (Sub-Document)
2. פרק (Chapter)
3. תת פרק (Sub-Chapter)
4. סעיף (Item/Section)

Each level provides:
- Base schema (for creation)
- Response schema (with computed totals)
- Nested schema (with child items)
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, computed_field


# =============================================================================
# Sub-Document Schemas (תת כתב) - Level 1
# =============================================================================

class BOQSubDocumentBase(BaseModel):
    """Base schema for BOQ Sub-Document creation."""
    code: str = Field(..., description="Sub-document code (e.g., '3')")
    name_he: str = Field(..., description="Hebrew name (e.g., 'חפירה ודיפון')")
    name_en: Optional[str] = Field(None, description="English name")
    description: Optional[str] = None
    display_order: int = 0


class BOQSubDocumentCreate(BOQSubDocumentBase):
    """Schema for creating a new sub-document."""
    project_id: int


class BOQSubDocumentUpdate(BaseModel):
    """Schema for updating a sub-document."""
    name_he: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class BOQSubDocumentSummary(BOQSubDocumentBase):
    """Summary response without nested items - for list views."""
    id: int
    project_id: int
    cached_total: float = Field(0, description="Cached total price")
    chapter_count: int = Field(0, description="Number of chapters")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Chapter Schemas (פרק) - Level 2
# =============================================================================

class BOQChapterBase(BaseModel):
    """Base schema for BOQ Chapter creation."""
    code: str = Field(..., description="Chapter code (e.g., '1')")
    name_he: str = Field(..., description="Hebrew name (e.g., 'עבודות עפר')")
    name_en: Optional[str] = Field(None, description="English name")
    full_code: Optional[str] = Field(None, description="Full code (e.g., '3.1')")
    dekel_chapter_code: Optional[str] = Field(None, description="Dekel pricing chapter")
    description: Optional[str] = None
    display_order: int = 0


class BOQChapterCreate(BOQChapterBase):
    """Schema for creating a new chapter."""
    sub_document_id: int


class BOQChapterUpdate(BaseModel):
    """Schema for updating a chapter."""
    name_he: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    dekel_chapter_code: Optional[str] = None
    display_order: Optional[int] = None


class BOQChapterSummary(BOQChapterBase):
    """Summary response without nested items."""
    id: int
    sub_document_id: int
    cached_total: float = Field(0, description="Cached total price")
    sub_chapter_count: int = Field(0, description="Number of sub-chapters")
    item_count: int = Field(0, description="Total items in chapter")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Sub-Chapter Schemas (תת פרק) - Level 3
# =============================================================================

class BOQSubChapterBase(BaseModel):
    """Base schema for BOQ Sub-Chapter creation."""
    code: str = Field(..., description="Sub-chapter code (e.g., '1')")
    name_he: str = Field(..., description="Hebrew name (e.g., 'עבודות הכנה ופרוק')")
    name_en: Optional[str] = Field(None, description="English name")
    full_code: Optional[str] = Field(None, description="Full code (e.g., '3.1.1')")
    description: Optional[str] = None
    display_order: int = 0


class BOQSubChapterCreate(BOQSubChapterBase):
    """Schema for creating a new sub-chapter."""
    chapter_id: int


class BOQSubChapterUpdate(BaseModel):
    """Schema for updating a sub-chapter."""
    name_he: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class BOQSubChapterSummary(BOQSubChapterBase):
    """Summary response without nested items."""
    id: int
    chapter_id: int
    cached_total: float = Field(0, description="Cached total price")
    item_count: int = Field(0, description="Number of items")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Item Schemas (סעיף) - Level 4 (Enhanced from existing)
# =============================================================================

class BOQItemHierarchyBase(BaseModel):
    """Base schema for BOQ Item with hierarchy support."""
    section_code: str = Field(..., description="Section code (e.g., '0010')")
    description_he: str = Field(..., description="Hebrew description")
    description_en: Optional[str] = None
    quantity: float = Field(..., ge=0, description="Item quantity")
    unit: str = Field(..., description="Unit of measure (e.g., 'מ\"ר')")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    total_price: float = Field(..., ge=0, description="Total price")
    dekel_code: Optional[str] = Field(None, description="Dekel catalog code")
    standard_reference: Optional[str] = Field(None, description="Israeli standard (e.g., 'ת\"י 466')")
    source_filename: Optional[str] = None
    source_layer: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    user_notes: Optional[str] = None


class BOQItemHierarchyCreate(BOQItemHierarchyBase):
    """Schema for creating a BOQ item with hierarchy."""
    project_id: int
    plan_id: Optional[int] = None
    sub_chapter_id: int


class BOQItemHierarchy(BOQItemHierarchyBase):
    """Response schema for BOQ item with hierarchy."""
    id: int
    project_id: int
    plan_id: Optional[int] = None
    sub_chapter_id: Optional[int] = None
    full_item_code: Optional[str] = Field(None, description="Full code (e.g., '3.1.1.0010')")
    is_deleted: bool = False
    is_modified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Nested Response Schemas (Full Hierarchy)
# =============================================================================

class BOQSubChapterWithItems(BOQSubChapterSummary):
    """Sub-chapter with all its items."""
    items: List[BOQItemHierarchy] = []


class BOQChapterWithSubChapters(BOQChapterSummary):
    """Chapter with all sub-chapters and their items."""
    sub_chapters: List[BOQSubChapterWithItems] = []


class BOQSubDocumentWithChapters(BOQSubDocumentSummary):
    """Full sub-document with complete hierarchy."""
    chapters: List[BOQChapterWithSubChapters] = []


class BOQHierarchySummary(BaseModel):
    """Summary totals for the entire BOQ."""
    subtotal: float = Field(0, description="Sum before VAT")
    vat_rate: float = Field(0.17, description="VAT rate (17% in Israel)")
    vat_amount: float = Field(0, description="VAT amount")
    grand_total: float = Field(0, description="Total including VAT")
    total_items: int = Field(0, description="Total number of items")
    total_chapters: int = Field(0, description="Total chapters")
    total_sub_chapters: int = Field(0, description="Total sub-chapters")


class BOQHierarchyResponse(BaseModel):
    """Complete hierarchical BOQ response."""
    project_id: int
    project_name: str
    date: str = Field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y"))
    sub_documents: List[BOQSubDocumentWithChapters] = []
    summary: BOQHierarchySummary

    class Config:
        from_attributes = True


# =============================================================================
# PDF Export Schema
# =============================================================================

class BOQPDFExportRequest(BaseModel):
    """Request schema for hierarchical PDF export."""
    project_id: int
    include_summary_page: bool = Field(True, description="Include summary page with chapter totals")
    include_sub_totals: bool = Field(True, description="Include sub-totals for each level")
    include_vat: bool = Field(True, description="Include VAT calculations")
    company_name: Optional[str] = Field(None, description="Company name for header")
    project_manager: Optional[str] = Field(None, description="Project manager name")
    tender_number: Optional[str] = Field(None, description="Tender/bid number")
    is_confidential: bool = Field(False, description="Mark as confidential")


# =============================================================================
# Helper Functions
# =============================================================================

def build_hierarchy_response(
    db,  # SQLAlchemy Session
    project_id: int,
    include_deleted: bool = False,
    vat_rate: float = 0.17
) -> dict:
    """
    Build a complete hierarchy response by querying the database.

    Args:
        db: SQLAlchemy database session
        project_id: Project ID
        include_deleted: Include soft-deleted items
        vat_rate: VAT rate (default 17%)

    Returns:
        dict with hierarchical BOQ data
    """
    # Import models here to avoid circular import
    from app import models

    # Get project
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return None

    # Get all sub-documents with nested data
    sub_docs = db.query(models.BOQSubDocument).filter(
        models.BOQSubDocument.project_id == project_id
    ).order_by(models.BOQSubDocument.display_order).all()

    sub_documents_data = []
    subtotal = 0.0
    total_items = 0
    total_chapters = 0
    total_sub_chapters = 0

    for sd in sub_docs:
        sd_data = {
            "id": sd.id,
            "code": sd.code,
            "name_he": sd.name_he,
            "name_en": sd.name_en,
            "display_order": sd.display_order,
            "cached_total": sd.cached_total or 0,
            "chapter_count": len(sd.chapters) if sd.chapters else 0,
            "project_id": sd.project_id,
            "created_at": sd.created_at,
            "updated_at": sd.updated_at,
            "chapters": []
        }

        for ch in sorted(sd.chapters, key=lambda x: x.display_order):
            total_chapters += 1
            ch_data = {
                "id": ch.id,
                "code": ch.code,
                "name_he": ch.name_he,
                "name_en": ch.name_en,
                "full_code": ch.full_code,
                "dekel_chapter_code": ch.dekel_chapter_code,
                "display_order": ch.display_order,
                "cached_total": ch.cached_total or 0,
                "sub_chapter_count": len(ch.sub_chapters) if ch.sub_chapters else 0,
                "item_count": 0,
                "sub_document_id": ch.sub_document_id,
                "created_at": ch.created_at,
                "updated_at": ch.updated_at,
                "sub_chapters": []
            }

            for sc in sorted(ch.sub_chapters, key=lambda x: x.display_order):
                total_sub_chapters += 1
                items_query = db.query(models.BOQItem).filter(
                    models.BOQItem.sub_chapter_id == sc.id
                )
                if not include_deleted:
                    items_query = items_query.filter(models.BOQItem.is_deleted == False)

                items = items_query.order_by(models.BOQItem.section_code).all()

                items_data = []
                for item in items:
                    total_items += 1
                    subtotal += item.total_price or 0
                    items_data.append({
                        "id": item.id,
                        "section_code": item.section_code,
                        "description_he": item.description_he,
                        "description_en": item.description_en,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "dekel_code": item.dekel_code,
                        "standard_reference": item.standard_reference,
                        "source_filename": item.source_filename,
                        "source_layer": item.source_layer,
                        "confidence": item.confidence,
                        "user_notes": item.user_notes,
                        "full_item_code": item.full_item_code,
                        "is_deleted": item.is_deleted,
                        "is_modified": item.is_modified,
                        "project_id": item.project_id,
                        "plan_id": item.plan_id,
                        "sub_chapter_id": item.sub_chapter_id,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at
                    })

                ch_data["item_count"] += len(items_data)

                sc_data = {
                    "id": sc.id,
                    "code": sc.code,
                    "name_he": sc.name_he,
                    "name_en": sc.name_en,
                    "full_code": sc.full_code,
                    "display_order": sc.display_order,
                    "cached_total": sc.cached_total or 0,
                    "item_count": len(items_data),
                    "chapter_id": sc.chapter_id,
                    "created_at": sc.created_at,
                    "updated_at": sc.updated_at,
                    "items": items_data
                }
                ch_data["sub_chapters"].append(sc_data)

            sd_data["chapters"].append(ch_data)

        sub_documents_data.append(sd_data)

    # Calculate VAT
    vat_amount = subtotal * vat_rate
    grand_total = subtotal + vat_amount

    return {
        "project_id": project_id,
        "project_name": project.name,
        "date": datetime.now().strftime("%d/%m/%Y"),
        "sub_documents": sub_documents_data,
        "summary": {
            "subtotal": subtotal,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "grand_total": grand_total,
            "total_items": total_items,
            "total_chapters": total_chapters,
            "total_sub_chapters": total_sub_chapters
        }
    }
