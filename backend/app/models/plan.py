from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectPlan(Base):
    __tablename__ = "project_plan"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=True)  # Optional project association
    filename = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Integer, default=0)  # 0-100
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Store the full GPT-4 generated Israeli BOQ as JSON
    boq_data = Column(Text, nullable=True)  # JSON string of full BOQ with Dekel pricing
    boq_subtotal = Column(Float, nullable=True)  # Total before VAT
    boq_vat_amount = Column(Float, nullable=True)  # VAT amount
    boq_grand_total = Column(Float, nullable=True)  # Total with VAT

    # AutoCAD extraction summary
    extraction_data = Column(Text, nullable=True)  # JSON summary of what was extracted from DWG

    owner = relationship("User", backref="plans")
    project = relationship("Project", back_populates="plans")
    materials = relationship("MaterialQuantity", back_populates="plan", cascade="all, delete-orphan")
    extraction_layers = relationship("ProjectExtractionLayer", back_populates="plan", cascade="all, delete-orphan")
    boq_items = relationship("BOQItem", back_populates="plan", cascade="all, delete-orphan")
