from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ExtractionLayerBase(BaseModel):
    """Base schema for extraction layer."""
    layer_name: str
    area_m2: float = 0.0
    polyline_count: int = 0
    hatch_count: int = 0
    auto_category: str = "review"  # 'include', 'exclude', 'review'


class ExtractionLayerCreate(ExtractionLayerBase):
    """Schema for creating an extraction layer."""
    plan_id: int


class ExtractionLayerUpdate(BaseModel):
    """Schema for updating user selection."""
    user_selected: Optional[bool] = None


class ExtractionLayer(ExtractionLayerBase):
    """Schema for returning extraction layer."""
    id: int
    plan_id: int
    user_selected: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExtractionLayerSummary(BaseModel):
    """Summary of extraction layers for a plan."""
    plan_id: int
    filename: str
    layers: List[ExtractionLayer]
    totals: dict


class BulkLayerSelectionRequest(BaseModel):
    """Request to update multiple layer selections at once."""
    selected_layer_names: List[str]  # Layers to include
    deselected_layer_names: Optional[List[str]] = None  # Layers to exclude
