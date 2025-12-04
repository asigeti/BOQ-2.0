"""
Pydantic schemas for BOQ items
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class BOQItemBase(BaseModel):
    """Base schema for BOQ item"""
    chapter_code: str
    chapter_name_he: str
    chapter_name_en: Optional[str] = None
    item_code: str
    description_he: str
    description_en: Optional[str] = None
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    source_filename: Optional[str] = None
    source_layer: Optional[str] = None
    confidence: Optional[float] = None
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
