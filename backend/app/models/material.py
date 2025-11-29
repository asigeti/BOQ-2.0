from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class MaterialQuantity(Base):
    __tablename__ = "material_quantity"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id"))
    material_name = Column(String, index=True)
    quantity = Column(Float)
    unit = Column(String)
    confidence_score = Column(Float)

    plan = relationship("ProjectPlan", backref="materials")
