from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectExtractionLayer(Base):
    """
    Stores extracted AutoCAD layer data with area calculations.
    Each row represents one layer from a DWG file extraction.
    FK to ProjectPlan (which has FK to Project).
    """
    __tablename__ = "project_extraction_layer"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id", ondelete="CASCADE"), nullable=False, index=True)

    # Layer identification
    layer_name = Column(String, nullable=False)

    # Extracted geometry data (already in m²)
    area_m2 = Column(Float, default=0.0)
    polyline_count = Column(Integer, default=0)
    hatch_count = Column(Integer, default=0)

    # Auto-categorization based on layer name patterns
    # Values: 'include', 'exclude', 'review'
    auto_category = Column(String, default="review")

    # User selection (after review)
    # None = not reviewed, True = include, False = exclude
    user_selected = Column(Boolean, nullable=True, default=None)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan = relationship("ProjectPlan", back_populates="extraction_layers")

    def __repr__(self):
        return f"<ExtractionLayer {self.layer_name}: {self.area_m2:.2f} m²>"
