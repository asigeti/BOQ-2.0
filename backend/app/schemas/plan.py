from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class PlanBase(BaseModel):
    filename: str
    file_type: str

class PlanCreate(PlanBase):
    pass

class Plan(PlanBase):
    id: int
    user_id: int
    file_path: str
    processing_status: str = "pending"
    processing_progress: int = 0
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Alias for API responses
PlanOut = Plan
