"""
BOQ Hierarchy Models - Israeli BOQ 4-Level Structure
=====================================================

Implements the professional Israeli BOQ hierarchy:
1. תת כתב (Sub-Document) - e.g., "3" = "חפירה ודיפון"
2. פרק (Chapter) - e.g., "1" = "עבודות עפר"
3. תת פרק (Sub-Chapter) - e.g., "1.1" = "עבודות הכנה ופרוק"
4. סעיף (Item) - e.g., "3.1.1.0010" = individual priced item

This structure follows the מחירון דקל and הספר הכחול standards.

GENERIC DESIGN: Names and codes are user-defined, making this suitable for:
- Construction projects (בניה)
- Infrastructure projects (תשתיות)
- Any industry requiring hierarchical BOQ
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class BOQSubDocument(Base):
    """
    Sub-Document level (תת כתב) - Highest level in BOQ hierarchy.

    Example: "3" = "חפירה ודיפון" (Excavation and Shoring)

    This is the first part of the 4-part code: {sub_doc}.{chapter}.{sub_chapter}.{item}

    Usage:
    - Groups related work types under one sub-document
    - Provides top-level summary totals for tender evaluation
    - Maps to major work categories in Dekel pricing
    """
    __tablename__ = "boq_sub_document"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    # Code and naming - GENERIC (not hardcoded)
    code = Column(String(10), nullable=False)  # "3", "4", etc.
    name_he = Column(String(300), nullable=False)  # "חפירה ודיפון"
    name_en = Column(String(300), nullable=True)   # "Excavation and Shoring"

    # Sorting/display order within project
    display_order = Column(Integer, default=0)

    # Optional metadata
    description = Column(Text, nullable=True)  # Extended description

    # Cached total for performance (updated on item changes)
    cached_total = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="boq_sub_documents")
    chapters = relationship("BOQChapter", back_populates="sub_document",
                           cascade="all, delete-orphan",
                           order_by="BOQChapter.display_order")

    # Unique constraint: one code per project
    __table_args__ = (
        UniqueConstraint('project_id', 'code', name='uq_sub_doc_project_code'),
    )

    def compute_total(self) -> float:
        """Calculate sum of all chapter totals under this sub-document."""
        return sum(ch.compute_total() for ch in self.chapters)

    def update_cached_total(self):
        """Update the cached total from child chapters."""
        self.cached_total = self.compute_total()


class BOQChapter(Base):
    """
    Chapter level (פרק) - Second level in BOQ hierarchy.

    Example: "1" = "עבודות עפר" under sub-document "3"
    Full code: "3.1" (sub_doc.chapter)

    Usage:
    - Groups related work items by trade/specialty
    - Provides chapter-level summary for cost breakdown
    - Maps to Dekel chapter codes (01-46)
    """
    __tablename__ = "boq_chapter"

    id = Column(Integer, primary_key=True, index=True)
    sub_document_id = Column(Integer, ForeignKey("boq_sub_document.id",
                                                  ondelete="CASCADE"),
                             nullable=False, index=True)

    # Code and naming
    code = Column(String(10), nullable=False)  # "1", "2", etc. (within sub-doc)
    name_he = Column(String(300), nullable=False)  # "עבודות עפר"
    name_en = Column(String(300), nullable=True)   # "Earthworks"

    # Full code for display (computed: sub_doc.chapter)
    full_code = Column(String(20), nullable=True)  # "3.1"

    # Reference to Dekel pricing chapter (for price lookups)
    dekel_chapter_code = Column(String(10), nullable=True)  # "01", "02" etc.

    # Sorting/display order within sub-document
    display_order = Column(Integer, default=0)

    # Optional metadata
    description = Column(Text, nullable=True)

    # Cached total for performance
    cached_total = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sub_document = relationship("BOQSubDocument", back_populates="chapters")
    sub_chapters = relationship("BOQSubChapter", back_populates="chapter",
                                cascade="all, delete-orphan",
                                order_by="BOQSubChapter.display_order")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('sub_document_id', 'code', name='uq_chapter_subdoc_code'),
    )

    def compute_total(self) -> float:
        """Calculate sum of all sub-chapter totals under this chapter."""
        return sum(sc.compute_total() for sc in self.sub_chapters)

    def update_cached_total(self):
        """Update the cached total from child sub-chapters."""
        self.cached_total = self.compute_total()

    def generate_full_code(self) -> str:
        """Generate the full hierarchical code."""
        if self.sub_document:
            return f"{self.sub_document.code}.{self.code}"
        return self.code


class BOQSubChapter(Base):
    """
    Sub-Chapter level (תת פרק) - Third level in BOQ hierarchy.

    Example: "1.1" = "עבודות הכנה ופרוק" under chapter "1"
    Full code: "3.1.1" (sub_doc.chapter.sub_chapter)

    Usage:
    - Groups related work items by specific activity type
    - Provides sub-chapter summary for detailed cost analysis
    - Allows fine-grained categorization within a chapter
    """
    __tablename__ = "boq_sub_chapter"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("boq_chapter.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    # Code and naming
    code = Column(String(10), nullable=False)  # "1", "2", etc. (within chapter)
    name_he = Column(String(300), nullable=False)  # "עבודות הכנה ופרוק"
    name_en = Column(String(300), nullable=True)   # "Preparation and Demolition"

    # Full code for display (computed: sub_doc.chapter.sub_chapter)
    full_code = Column(String(30), nullable=True)  # "3.1.1"

    # Sorting/display order within chapter
    display_order = Column(Integer, default=0)

    # Optional metadata
    description = Column(Text, nullable=True)

    # Cached total for performance
    cached_total = Column(Float, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    chapter = relationship("BOQChapter", back_populates="sub_chapters")
    items = relationship("BOQItem", back_populates="sub_chapter",
                        cascade="all, delete-orphan",
                        order_by="BOQItem.section_code")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('chapter_id', 'code', name='uq_subchapter_chapter_code'),
    )

    def compute_total(self) -> float:
        """Calculate sum of all item totals under this sub-chapter."""
        return sum(item.total_price for item in self.items if not item.is_deleted)

    def update_cached_total(self):
        """Update the cached total from child items."""
        self.cached_total = self.compute_total()

    def generate_full_code(self) -> str:
        """Generate the full hierarchical code."""
        if self.chapter:
            chapter_full = self.chapter.generate_full_code()
            return f"{chapter_full}.{self.code}"
        return self.code


# ============================================================================
# Helper functions for hierarchy management
# ============================================================================

def get_or_create_sub_document(db, project_id: int, code: str, name_he: str,
                                name_en: str = None) -> BOQSubDocument:
    """Get existing sub-document or create new one."""
    existing = db.query(BOQSubDocument).filter(
        BOQSubDocument.project_id == project_id,
        BOQSubDocument.code == code
    ).first()

    if existing:
        return existing

    sub_doc = BOQSubDocument(
        project_id=project_id,
        code=code,
        name_he=name_he,
        name_en=name_en or "",
        display_order=int(code) if code.isdigit() else 0
    )
    db.add(sub_doc)
    db.flush()
    return sub_doc


def get_or_create_chapter(db, sub_document_id: int, code: str, name_he: str,
                          name_en: str = None, dekel_code: str = None) -> BOQChapter:
    """Get existing chapter or create new one."""
    existing = db.query(BOQChapter).filter(
        BOQChapter.sub_document_id == sub_document_id,
        BOQChapter.code == code
    ).first()

    if existing:
        return existing

    # Get sub-document for full code
    sub_doc = db.query(BOQSubDocument).get(sub_document_id)

    chapter = BOQChapter(
        sub_document_id=sub_document_id,
        code=code,
        name_he=name_he,
        name_en=name_en or "",
        full_code=f"{sub_doc.code}.{code}" if sub_doc else code,
        dekel_chapter_code=dekel_code,
        display_order=int(code) if code.isdigit() else 0
    )
    db.add(chapter)
    db.flush()
    return chapter


def get_or_create_sub_chapter(db, chapter_id: int, code: str, name_he: str,
                               name_en: str = None) -> BOQSubChapter:
    """Get existing sub-chapter or create new one."""
    existing = db.query(BOQSubChapter).filter(
        BOQSubChapter.chapter_id == chapter_id,
        BOQSubChapter.code == code
    ).first()

    if existing:
        return existing

    # Get chapter for full code
    chapter = db.query(BOQChapter).get(chapter_id)

    sub_chapter = BOQSubChapter(
        chapter_id=chapter_id,
        code=code,
        name_he=name_he,
        name_en=name_en or "",
        full_code=f"{chapter.full_code}.{code}" if chapter else code,
        display_order=int(code) if code.isdigit() else 0
    )
    db.add(sub_chapter)
    db.flush()
    return sub_chapter


def update_hierarchy_totals(db, sub_chapter_id: int):
    """
    Update cached totals for entire hierarchy chain.
    Call this after adding/updating/deleting BOQ items.
    """
    sub_chapter = db.query(BOQSubChapter).get(sub_chapter_id)
    if not sub_chapter:
        return

    # Update sub-chapter total
    sub_chapter.update_cached_total()

    # Update chapter total
    chapter = sub_chapter.chapter
    if chapter:
        chapter.update_cached_total()

        # Update sub-document total
        sub_doc = chapter.sub_document
        if sub_doc:
            sub_doc.update_cached_total()

    db.flush()


def parse_item_code(code: str) -> dict:
    """
    Parse a hierarchical item code into its components.

    Examples:
    - "3.1.1.0010" -> {"sub_doc": "3", "chapter": "1", "sub_chapter": "1", "section": "0010"}
    - "01.01.01" -> {"sub_doc": None, "chapter": "01", "sub_chapter": "01", "section": "01"}

    Returns dict with parsed components, None values for missing parts.
    """
    if not code:
        return {"sub_doc": None, "chapter": None, "sub_chapter": None, "section": None}

    parts = code.split('.')

    if len(parts) >= 4:
        # Full 4-part code: sub_doc.chapter.sub_chapter.section
        return {
            "sub_doc": parts[0],
            "chapter": parts[1],
            "sub_chapter": parts[2],
            "section": parts[3]
        }
    elif len(parts) == 3:
        # Legacy 3-part code: chapter.sub_chapter.section
        return {
            "sub_doc": None,
            "chapter": parts[0],
            "sub_chapter": parts[1],
            "section": parts[2]
        }
    elif len(parts) == 2:
        # 2-part code: chapter.section
        return {
            "sub_doc": None,
            "chapter": parts[0],
            "sub_chapter": "1",
            "section": parts[1]
        }
    else:
        # Single part - treat as section
        return {
            "sub_doc": None,
            "chapter": "01",
            "sub_chapter": "1",
            "section": parts[0]
        }


def generate_hierarchical_item_code(sub_doc_code: str, chapter_code: str,
                                     sub_chapter_code: str, section_code: str) -> str:
    """
    Generate a full hierarchical item code.

    Format: {sub_doc}.{chapter}.{sub_chapter}.{section}
    Example: 3.1.1.0010
    """
    return f"{sub_doc_code}.{chapter_code}.{sub_chapter_code}.{section_code}"
