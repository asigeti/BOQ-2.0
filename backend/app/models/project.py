from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    """
    Project model - contains multiple DWG files and generates aggregated BOQ.
    """
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    folder_path = Column(String, nullable=True)  # Source folder for DWG scanning
    user_id = Column(Integer, ForeignKey("user.id"), default=1)

    # Building parameters for BOQ calculation
    building_area = Column(Float, nullable=True)  # User-specified building area in m²
    expected_total = Column(Float, nullable=True)  # Expected BOQ total for calibration

    # Processing status
    processing_status = Column(String, default="pending")  # pending, scanning, processing, completed, failed
    processing_progress = Column(Integer, default=0)  # 0-100
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", backref="projects")
    plans = relationship("ProjectPlan", back_populates="project", cascade="all, delete-orphan")
    boq_items = relationship("BOQItem", back_populates="project", cascade="all, delete-orphan")
    # Hierarchical BOQ structure
    boq_sub_documents = relationship("BOQSubDocument", back_populates="project",
                                     cascade="all, delete-orphan",
                                     order_by="BOQSubDocument.display_order")
