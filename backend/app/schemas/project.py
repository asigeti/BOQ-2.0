from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    folder_path: Optional[str] = None
    building_area: Optional[float] = None  # Building area in m² for BOQ calculation
    expected_total: Optional[float] = None  # Expected BOQ total for calibration


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    folder_path: Optional[str] = None
    building_area: Optional[float] = None
    expected_total: Optional[float] = None


class ProjectScanRequest(BaseModel):
    folder_path: str


class ProjectPlanSummary(BaseModel):
    id: int
    filename: str
    file_type: str
    processing_status: str
    processing_progress: int

    class Config:
        from_attributes = True


class Project(ProjectBase):
    id: int
    folder_path: Optional[str]
    building_area: Optional[float] = None
    expected_total: Optional[float] = None
    processing_status: str
    processing_progress: int
    total_files: int
    processed_files: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectWithPlans(Project):
    plans: List[ProjectPlanSummary] = []


class FolderScanResult(BaseModel):
    folder_path: str
    dwg_files: List[str]
    total_count: int


class ExtractionSelectionRequest(BaseModel):
    """Request body for confirming extraction layer selection."""
    selected_layer_ids: List[int]  # Layer IDs to include in BOQ (unique across all files)
    custom_area_m2: Optional[float] = None  # Optional manual area override
