from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProjectPlan(Base):
    __tablename__ = "project_plan"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Integer, default=0)  # 0-100
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", backref="plans")
    project = relationship("Project", back_populates="plans")
    boq_items = relationship("BOQItem", back_populates="plan")
    extraction_layers = relationship("ProjectExtractionLayer", back_populates="plan", cascade="all, delete-orphan")
