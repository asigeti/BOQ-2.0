"""
BOQ (Bill of Quantities) Item Model
====================================

Stores individual line items (סעיפים) in the BOQ with:
- Full hierarchical structure support (תת כתב → פרק → תת פרק → סעיף)
- Source tracking from DWG/PDF files
- User modifications and notes
- Backward compatibility with flat structure

Item code format: {sub_doc}.{chapter}.{sub_chapter}.{section}
Example: 3.1.1.0010 = תת כתב 3, פרק 1, תת פרק 1, סעיף 0010
"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class BOQItem(Base):
    """
    BOQ line item (סעיף) - Lowest level in 4-tier hierarchy.

    Example: "3.1.1.0010" = Individual priced item

    Supports both:
    1. New hierarchical structure (via sub_chapter_id FK)
    2. Legacy flat structure (via chapter_code, item_code) for backward compatibility
    """
    __tablename__ = "boq_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id", ondelete="CASCADE"),
                     nullable=True)  # Source file

    # =========================================================================
    # NEW: Hierarchical structure (4-level)
    # =========================================================================
    # FK to sub-chapter (תת פרק) - primary hierarchy relationship
    sub_chapter_id = Column(Integer, ForeignKey("boq_sub_chapter.id",
                                                 ondelete="SET NULL"),
                            nullable=True, index=True)

    # Section code within sub-chapter (e.g., "0010", "0020")
    section_code = Column(String(20), nullable=True)

    # Full hierarchical item code for display/search (e.g., "3.1.1.0010")
    full_item_code = Column(String(50), nullable=True, index=True)

    # =========================================================================
    # LEGACY: Flat structure (for backward compatibility)
    # =========================================================================
    # These fields are kept for existing data and gradual migration
    chapter_code = Column(String(10), nullable=True, index=True)  # e.g., "01", "02"
    chapter_name_he = Column(String(200), nullable=True)
    chapter_name_en = Column(String(200), nullable=True)
    item_code = Column(String(50), nullable=True)  # e.g., "01.001.0010"

    # =========================================================================
    # Item details
    # =========================================================================
    description_he = Column(Text, nullable=False)
    description_en = Column(Text, nullable=True)

    # Quantities and pricing (CRITICAL - must be accurate)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False)  # e.g., "מ״ר", "יח׳", "מ״ק"
    unit_price = Column(Float, nullable=False, default=0)
    total_price = Column(Float, nullable=False, default=0)

    # Dekel pricing reference
    dekel_code = Column(String(50), nullable=True)  # Dekel catalog code

    # Israeli standards reference (e.g., "ת\"י 466")
    standard_reference = Column(String(100), nullable=True)

    # =========================================================================
    # Source tracking
    # =========================================================================
    source_filename = Column(String(500), nullable=True)  # DWG/PDF filename
    source_layer = Column(String(500), nullable=True)  # Layer name
    confidence = Column(Float, nullable=True)  # AI confidence (0-1)

    # =========================================================================
    # User modifications
    # =========================================================================
    user_notes = Column(Text, nullable=True)  # User-added notes
    is_deleted = Column(Boolean, default=False)  # Soft delete
    is_modified = Column(Boolean, default=False)  # Track if user edited

    # =========================================================================
    # Metadata
    # =========================================================================
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # =========================================================================
    # Relationships
    # =========================================================================
    project = relationship("Project", back_populates="boq_items")
    plan = relationship("ProjectPlan", back_populates="boq_items")
    sub_chapter = relationship("BOQSubChapter", back_populates="items")

    def compute_full_code(self) -> str:
        """
        Compute the full hierarchical item code.

        Returns code like "3.1.1.0010" from hierarchy relationships,
        or falls back to legacy item_code.
        """
        if self.sub_chapter and self.section_code:
            return f"{self.sub_chapter.full_code}.{self.section_code}"
        # Fallback for legacy items
        return self.item_code or self.section_code or ""

    def get_hierarchy_path(self) -> dict:
        """
        Get the full hierarchy path for this item.

        Returns dict with all levels:
        {
            "sub_document": {"code": "3", "name": "חפירה ודיפון"},
            "chapter": {"code": "1", "name": "עבודות עפר"},
            "sub_chapter": {"code": "1", "name": "עבודות הכנה ופרוק"},
            "section": {"code": "0010", "description": "..."}
        }
        """
        if not self.sub_chapter:
            # Legacy flat item
            return {
                "sub_document": None,
                "chapter": {"code": self.chapter_code, "name": self.chapter_name_he},
                "sub_chapter": None,
                "section": {"code": self.item_code, "description": self.description_he}
            }

        chapter = self.sub_chapter.chapter
        sub_document = chapter.sub_document if chapter else None

        return {
            "sub_document": {
                "code": sub_document.code if sub_document else None,
                "name": sub_document.name_he if sub_document else None
            },
            "chapter": {
                "code": chapter.code if chapter else None,
                "name": chapter.name_he if chapter else None
            },
            "sub_chapter": {
                "code": self.sub_chapter.code,
                "name": self.sub_chapter.name_he
            },
            "section": {
                "code": self.section_code,
                "description": self.description_he
            }
        }
