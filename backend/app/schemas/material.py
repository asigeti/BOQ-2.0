from pydantic import BaseModel

class MaterialQuantityBase(BaseModel):
    material_name: str
    quantity: float
    unit: str
    confidence_score: float

class MaterialQuantityCreate(MaterialQuantityBase):
    plan_id: int

class MaterialQuantityOut(MaterialQuantityBase):
    id: int
    plan_id: int

    class Config:
        from_attributes = True
