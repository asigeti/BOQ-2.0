"""
Pydantic schemas for BOQ items
==============================

Supports both:
1. Legacy flat structure (chapter_code, item_code)
2. New hierarchical structure (sub_chapter_id, section_code, full_item_code)

Backward compatible - legacy fields are optional for new hierarchical items.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BOQItemBase(BaseModel):
    """
    Base schema for BOQ item - supports both legacy and hierarchical modes.

    Legacy mode: Uses chapter_code, chapter_name_he, item_code
    Hierarchical mode: Uses sub_chapter_id, section_code, full_item_code
    """
    # Legacy fields (optional for hierarchical items)
    chapter_code: Optional[str] = Field(None, description="Legacy: Chapter code (e.g., '01')")
    chapter_name_he: Optional[str] = Field(None, description="Legacy: Hebrew chapter name")
    chapter_name_en: Optional[str] = None
    item_code: Optional[str] = Field(None, description="Legacy: Item code (e.g., '01.001.0010')")

    # New hierarchical fields
    sub_chapter_id: Optional[int] = Field(None, description="FK to sub-chapter (תת פרק)")
    section_code: Optional[str] = Field(None, description="Section code within sub-chapter (e.g., '0010')")
    full_item_code: Optional[str] = Field(None, description="Full hierarchical code (e.g., '3.1.1.0010')")

    # Item details (required)
    description_he: str = Field(..., description="Hebrew description")
    description_en: Optional[str] = None
    quantity: float = Field(..., ge=0, description="Item quantity")
    unit: str = Field(..., description="Unit of measure")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    total_price: float = Field(..., ge=0, description="Total price")

    # Dekel pricing reference
    dekel_code: Optional[str] = Field(None, description="Dekel catalog code")

    # Israeli standards reference
    standard_reference: Optional[str] = Field(None, description="Israeli standard (e.g., 'ת\"י 466')")

    # Source tracking
    source_filename: Optional[str] = None
    source_layer: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    user_notes: Optional[str] = None


class BOQItemCreate(BOQItemBase):
    """Schema for creating a BOQ item"""
    project_id: int
    plan_id: Optional[int] = None


class BOQItemUpdate(BaseModel):
    """Schema for updating a BOQ item"""
    quantity: Optional[float] = None
    description_he: Optional[str] = None
    unit_price: Optional[float] = None
    user_notes: Optional[str] = None
    is_deleted: Optional[bool] = None
    # New fields that can be updated
    section_code: Optional[str] = None
    dekel_code: Optional[str] = None
    standard_reference: Optional[str] = None


class BOQItem(BOQItemBase):
    """Schema for returning a BOQ item"""
    id: int
    project_id: int
    plan_id: Optional[int] = None
    is_deleted: bool
    is_modified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BOQItemWithSource(BOQItem):
    """BOQ item with additional source file information"""
    pass


class BOQItemWithHierarchy(BOQItem):
    """
    BOQ item with full hierarchy path information.

    Includes resolved names for each level:
    - sub_document_name
    - chapter_name (from hierarchy)
    - sub_chapter_name
    """
    sub_document_code: Optional[str] = None
    sub_document_name: Optional[str] = None
    hierarchy_chapter_code: Optional[str] = None
    hierarchy_chapter_name: Optional[str] = None
    sub_chapter_code: Optional[str] = None
    sub_chapter_name: Optional[str] = None
