"""
BOQ (Bill of Quantities) Item Model
Stores individual line items in the BOQ with source tracking and user modifications.
"""
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class BOQItem(Base):
    """BOQ line item with source tracking and user notes."""
    __tablename__ = "boq_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id", ondelete="CASCADE"), nullable=True)  # Source file

    # Dekel BOQ fields
    chapter_code = Column(String(10), nullable=False, index=True)  # e.g., "01", "02"
    chapter_name_he = Column(String(200), nullable=False)
    chapter_name_en = Column(String(200), nullable=True)
    item_code = Column(String(50), nullable=False)  # e.g., "01.001.0010"
    description_he = Column(Text, nullable=False)
    description_en = Column(Text, nullable=True)

    # Quantities and pricing
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False)  # e.g., "מ״ר", "יח׳"
    unit_price = Column(Float, nullable=False, default=0)
    total_price = Column(Float, nullable=False, default=0)

    # Source tracking
    source_filename = Column(String(500), nullable=True)  # DWG filename
    source_layer = Column(String(500), nullable=True)  # Layer name
    confidence = Column(Float, nullable=True)  # AI confidence (0-1)

    # User modifications
    user_notes = Column(Text, nullable=True)  # User-added notes
    is_deleted = Column(Boolean, default=False)  # Soft delete
    is_modified = Column(Boolean, default=False)  # Track if user edited

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="boq_items")
    plan = relationship("ProjectPlan", back_populates="boq_items")
