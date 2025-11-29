# ConstructionAI Pro - Super Detailed Development Plan

**Document Version:** 1.0
**Created:** November 27, 2025
**Target Completion:** MVP Phase 1 (Months 1-6 per PRD)
**Status:** Planning Complete

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [PRD Gap Analysis](#2-prd-gap-analysis)
3. [Development Phases](#3-development-phases)
4. [Phase 1: Foundation & Critical Fixes](#4-phase-1-foundation--critical-fixes)
5. [Phase 2: Core AI Features](#5-phase-2-core-ai-features)
6. [Phase 3: Supply Chain & Weather](#6-phase-3-supply-chain--weather)
7. [Phase 4: Dashboard & Analytics](#7-phase-4-dashboard--analytics)
8. [Phase 5: Security & Compliance](#8-phase-5-security--compliance)
9. [Phase 6: Integration & Export](#9-phase-6-integration--export)
10. [Phase 7: Testing & Quality](#10-phase-7-testing--quality)
11. [Phase 8: Mobile & Field App](#11-phase-8-mobile--field-app)
12. [Technical Implementation Details](#12-technical-implementation-details)
13. [Database Schema Evolution](#13-database-schema-evolution)
14. [API Endpoints Roadmap](#14-api-endpoints-roadmap)
15. [Frontend Component Library](#15-frontend-component-library)
16. [DevOps & Infrastructure](#16-devops--infrastructure)
17. [Risk Mitigation](#17-risk-mitigation)

---

## 1. Current State Analysis

### 1.1 What's Already Built

| Feature | Status | Completeness |
|---------|--------|--------------|
| User Authentication | Implemented | 70% |
| File Upload | Implemented | 80% |
| PDF Material Extraction | Implemented | 60% |
| DXF/CAD Processing | Implemented | 40% |
| Supply Chain (Mock) | Implemented | 20% |
| Weather (Mock) | Implemented | 15% |
| Excel Export | Implemented | 90% |
| Dashboard UI | Implemented | 50% |
| Plan Detail View | Implemented | 60% |
| Database Schema | Implemented | 40% |

### 1.2 Technology Stack (Current)

**Backend:**
- FastAPI 0.104.1 with Python 3.11
- PostgreSQL 15 with SQLAlchemy 2.0
- Redis 7 (available, not utilized)
- OpenAI GPT-4o/GPT-3.5 for extraction

**Frontend:**
- Next.js 16.0.3 with React 19
- Material-UI 7.3.5
- Redux Toolkit 2.10.1
- Hebrew (RTL) support

**Infrastructure:**
- Docker & Docker Compose
- Local development ready
- No CI/CD pipeline yet

---

## 2. PRD Gap Analysis

### 2.1 MVP Features Gap (PRD Section 4.1)

#### 4.1.1 Intelligent Quantity Takeoffs
| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| DWG file support | Routes to DXF | Need native DWG parser |
| PDF support | Working with OpenAI | Needs accuracy improvements |
| BIM/IFC support | Not implemented | Full implementation needed |
| 95%+ accuracy | Not measured | Need metrics & validation |
| Export to Excel/CSV | Excel only | Add CSV, ERP formats |
| Version comparison | Not implemented | Full implementation needed |
| Processing time <5min | Not tracked | Need benchmarking |

#### 4.1.2 Supply Chain Optimization
| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| Supplier integrations | Mock data only | Need real API integrations |
| Lead time prediction | Mock | Need ML model |
| Bulk pricing optimization | Not implemented | Full implementation needed |
| Inventory alerts | Not implemented | Full implementation needed |
| ROI calculation | Not implemented | Full implementation needed |

#### 4.1.3 Weather-Integrated Planning
| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| 14-day forecast | 5-day mock | Real API + extended |
| Activity-specific requirements | Not implemented | Full implementation needed |
| Schedule integration | Not implemented | Full implementation needed |
| Historical analysis | Not implemented | Full implementation needed |
| Auto schedule suggestions | Not implemented | Full implementation needed |

#### 4.1.4 Real-time Waste Monitoring
| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| IoT integration | Not implemented | Full implementation needed |
| Real-time dashboard | Not implemented | Full implementation needed |
| Waste trend analysis | Not implemented | Full implementation needed |
| Photo documentation | Not implemented | Full implementation needed |
| Sustainability reports | Not implemented | Full implementation needed |

### 2.2 Non-Functional Requirements Gap (PRD Section 5)

| Requirement | Current Status | Gap |
|-------------|---------------|-----|
| Response time <3s | Not measured | Need benchmarking |
| 99.9% uptime | No monitoring | Need infrastructure |
| 1000+ concurrent users | Not tested | Load testing needed |
| AES-256 encryption | Not implemented | Full implementation needed |
| MFA authentication | Not implemented | Full implementation needed |
| SSO integration | Not implemented | Full implementation needed |
| SOC 2 compliance | Not implemented | Full implementation needed |
| RBAC permissions | Not implemented | Full implementation needed |
| Audit logging | Not implemented | Full implementation needed |

---

## 3. Development Phases

### Phase Overview

```
Phase 1: Foundation & Critical Fixes     [Week 1-2]
    └── Bug fixes, security, stability

Phase 2: Core AI Features                [Week 3-6]
    └── Improved extraction, BIM support, accuracy

Phase 3: Supply Chain & Weather          [Week 7-10]
    └── Real APIs, predictions, scheduling

Phase 4: Dashboard & Analytics           [Week 11-14]
    └── KPI dashboards, visualizations, reports

Phase 5: Security & Compliance           [Week 15-18]
    └── MFA, RBAC, encryption, audit logs

Phase 6: Integration & Export            [Week 19-22]
    └── ERP integration, data sync, APIs

Phase 7: Testing & Quality               [Week 23-24]
    └── E2E tests, load tests, documentation

Phase 8: Mobile & Field App              [Week 25-26]
    └── React Native app, offline support
```

---

## 4. Phase 1: Foundation & Critical Fixes

### 4.1 Critical Bug Fixes

#### Task 1.1.1: Fix Frontend Build Error
**Priority:** CRITICAL | **Effort:** 15 minutes

**Files to modify:**
- `frontend/src/app/dashboard/plans/[id]/page.tsx`

**Changes:**
```typescript
// Line 18-19: Remove duplicate LinearProgress import
// Before:
LinearProgress,
LinearProgress,

// After:
LinearProgress,
```

#### Task 1.1.2: Fix Pydantic Deprecation
**Priority:** HIGH | **Effort:** 15 minutes

**Files to modify:**
- `backend/app/schemas/user.py`
- `backend/app/schemas/material.py`

**Changes:**
```python
# Change orm_mode to from_attributes
class Config:
    from_attributes = True  # was: orm_mode = True
```

#### Task 1.1.3: Fix Duplicate Import
**Priority:** LOW | **Effort:** 5 minutes

**Files to modify:**
- `backend/app/models/plan.py`

**Changes:**
```python
# Remove duplicate line 2
from datetime import datetime  # Keep only one
```

### 4.2 Security Fixes

#### Task 1.2.1: Secure File Upload
**Priority:** HIGH | **Effort:** 2 hours

**Files to modify:**
- `backend/app/api/endpoints/plans.py`

**Implementation:**
```python
import uuid
import os
from pathlib import Path

ALLOWED_EXTENSIONS = {'.pdf', '.dwg', '.dxf', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate file type and size"""
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {ext} not allowed"

    # Check file size (read content-length header)
    return True, ""

def sanitize_filename(filename: str) -> str:
    """Generate safe filename with UUID"""
    ext = Path(filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"

@router.post("/upload", response_model=schemas.Plan)
def upload_plan(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
) -> Any:
    # Validate file
    is_valid, error = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Generate safe filename
    safe_filename = sanitize_filename(file.filename)
    file_location = os.path.join(UPLOAD_DIR, safe_filename)

    # ... rest of implementation
```

#### Task 1.2.2: Environment-Based Configuration
**Priority:** HIGH | **Effort:** 1 hour

**Files to modify:**
- `backend/app/core/config.py`
- Create `backend/.env.example`

**Implementation:**
```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ConstructionAI Pro"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""

    # Security - MUST be set in production
    SECRET_KEY: str  # No default - must be provided
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Database
    DATABASE_URL: str

    # AI
    OPENAI_API_KEY: Optional[str] = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        case_sensitive = True
        env_file = ".env"

# .env.example
"""
SECRET_KEY=your-super-secret-key-minimum-32-characters
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
OPENAI_API_KEY=sk-your-openai-api-key
REDIS_URL=redis://localhost:6379
"""
```

### 4.3 Data Model Fixes

#### Task 1.3.1: Fix Materials Relationship
**Priority:** HIGH | **Effort:** 30 minutes

**Files to modify:**
- `backend/app/models/material.py`
- `backend/app/models/plan.py`

**Implementation:**
```python
# material.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class MaterialQuantity(Base):
    __tablename__ = "material_quantity"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id"), nullable=False)
    material_name = Column(String, index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    confidence_score = Column(Float, default=0.0)

    # Relationship
    plan = relationship("ProjectPlan", back_populates="materials")

# plan.py
from sqlalchemy.orm import relationship

class ProjectPlan(Base):
    __tablename__ = "project_plan"

    # ... existing columns ...

    # Relationships
    owner = relationship("User", backref="plans")
    materials = relationship("MaterialQuantity", back_populates="plan", cascade="all, delete-orphan")
```

#### Task 1.3.2: Fix Date Field Naming
**Priority:** HIGH | **Effort:** 20 minutes

**Files to modify:**
- `backend/app/schemas/plan.py` OR
- `frontend/src/app/dashboard/page.tsx`

**Option A - Backend Schema (Recommended):**
```python
# plan.py schema
from pydantic import Field

class Plan(PlanBase):
    id: int
    user_id: int
    file_path: str
    processing_status: str = "pending"
    processing_progress: int = 0
    uploaded_at: datetime
    upload_date: datetime = Field(alias="uploaded_at")  # Add alias

    class Config:
        from_attributes = True
        populate_by_name = True
```

**Option B - Frontend Interface:**
```typescript
// page.tsx
interface Plan {
    id: number;
    filename: string;
    uploaded_at: string;  // Match backend
}

// Update usage:
{new Date(plan.uploaded_at).toLocaleDateString('he-IL')}
```

### 4.4 Infrastructure Setup

#### Task 1.4.1: Database Migrations with Alembic
**Priority:** HIGH | **Effort:** 2 hours

**New files to create:**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/`

**Setup steps:**
```bash
cd backend
pip install alembic
alembic init alembic

# Configure alembic.ini
sqlalchemy.url = driver://user:pass@localhost/dbname

# Edit alembic/env.py to import models
from app.db.base import Base
from app.models import *  # Import all models
target_metadata = Base.metadata

# Create initial migration
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

#### Task 1.4.2: Logging Configuration
**Priority:** MEDIUM | **Effort:** 1 hour

**New file to create:**
- `backend/app/core/logging.py`

**Implementation:**
```python
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Configure application logging"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log"),
        ]
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    return logging.getLogger("constructionai")

# Usage in main.py
from app.core.logging import setup_logging
logger = setup_logging()
logger.info("Application starting...")
```

---

## 5. Phase 2: Core AI Features

### 5.1 Enhanced PDF Extraction

#### Task 2.1.1: Improve OpenAI Extraction Prompts
**Priority:** HIGH | **Effort:** 4 hours

**Files to modify:**
- `backend/app/services/extraction/pdf_extractor.py`

**Implementation:**
```python
# Enhanced prompts for better accuracy
SYSTEM_PROMPT_VISION = """You are an expert construction estimator and quantity surveyor.
Analyze the provided construction plan images with extreme precision.

Your task:
1. Identify ALL construction materials visible in the plans
2. Calculate accurate quantities based on dimensions shown
3. Use standard construction units (m2, m3, kg, pieces, etc.)
4. Provide confidence scores based on clarity of information

Material categories to look for:
- Concrete (foundations, slabs, columns, beams)
- Steel/Rebar (reinforcement, structural steel)
- Masonry (blocks, bricks, stone)
- Lumber/Wood (framing, finishing)
- Drywall/Plaster
- Roofing materials
- Windows and doors
- Plumbing fixtures
- Electrical components
- Finishing materials (paint, tiles, flooring)

Output format: JSON array only, no explanation text."""

EXTRACTION_PROMPT = """Extract ALL material quantities from these construction plans.

For each material found, provide:
{
    "material_name": "Specific material name",
    "quantity": <numeric value>,
    "unit": "standard unit (m2, m3, kg, pcs, lm)",
    "confidence_score": <0.0-1.0 based on clarity>,
    "location": "where in building (optional)",
    "notes": "any relevant details (optional)"
}

Rules:
1. Be thorough - include ALL materials you can identify
2. Use metric units preferably
3. Round quantities to 2 decimal places
4. Higher confidence = clearer visibility in plans
5. Include dimensions in notes if visible

Return ONLY a valid JSON array."""
```

#### Task 2.1.2: Multi-Page PDF Processing
**Priority:** HIGH | **Effort:** 3 hours

**Implementation:**
```python
async def extract_from_pdf_async(file_path: str) -> List[Dict]:
    """
    Enhanced PDF extraction with multi-page support and batching
    """
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)

    # Process pages in batches of 5
    batch_size = 5
    all_materials = []

    for batch_start in range(0, total_pages, batch_size):
        batch_end = min(batch_start + batch_size, total_pages)
        batch_pages = reader.pages[batch_start:batch_end]

        # Extract text and images from batch
        batch_text = ""
        batch_images = []

        for page in batch_pages:
            page_text = page.extract_text() or ""
            batch_text += page_text + "\n"

            for img in page.images:
                batch_images.append(img.data)

        # Process batch
        batch_materials = await process_batch(batch_text, batch_images)
        all_materials.extend(batch_materials)

    # Deduplicate and merge similar materials
    merged_materials = merge_duplicate_materials(all_materials)

    return merged_materials

def merge_duplicate_materials(materials: List[Dict]) -> List[Dict]:
    """Merge duplicate material entries"""
    merged = {}

    for mat in materials:
        key = (mat['material_name'].lower(), mat['unit'].lower())

        if key in merged:
            # Sum quantities, average confidence
            merged[key]['quantity'] += mat['quantity']
            merged[key]['confidence_score'] = (
                merged[key]['confidence_score'] + mat['confidence_score']
            ) / 2
        else:
            merged[key] = mat.copy()

    return list(merged.values())
```

### 5.2 BIM/IFC Support

#### Task 2.2.1: IFC File Parser
**Priority:** HIGH | **Effort:** 8 hours

**New file to create:**
- `backend/app/services/extraction/ifc_extractor.py`

**Dependencies to add:**
```
ifcopenshell==0.7.0
```

**Implementation:**
```python
import ifcopenshell
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def extract_from_ifc(file_path: str) -> List[Dict]:
    """
    Extract material quantities from BIM/IFC files
    """
    try:
        ifc_file = ifcopenshell.open(file_path)
        materials = []

        # Extract building elements
        element_types = [
            ('IfcWall', 'Wall'),
            ('IfcSlab', 'Slab'),
            ('IfcBeam', 'Beam'),
            ('IfcColumn', 'Column'),
            ('IfcDoor', 'Door'),
            ('IfcWindow', 'Window'),
            ('IfcRoof', 'Roof'),
            ('IfcStair', 'Stair'),
        ]

        for ifc_type, name in element_types:
            elements = ifc_file.by_type(ifc_type)

            for element in elements:
                # Get quantities
                quantity_data = extract_element_quantities(element)

                if quantity_data:
                    materials.append({
                        'material_name': f"{name} - {element.Name or 'Unnamed'}",
                        'quantity': quantity_data['quantity'],
                        'unit': quantity_data['unit'],
                        'confidence_score': 0.95,  # BIM data is highly accurate
                        'source': 'BIM/IFC',
                        'element_id': element.GlobalId
                    })

        # Extract material definitions
        material_defs = ifc_file.by_type('IfcMaterial')
        for mat_def in material_defs:
            # Process material definitions
            pass

        return materials

    except Exception as e:
        logger.error(f"IFC extraction failed: {e}")
        return []

def extract_element_quantities(element) -> Dict:
    """Extract quantity data from IFC element"""
    try:
        # Get quantity sets
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                property_set = definition.RelatingPropertyDefinition

                if property_set.is_a('IfcElementQuantity'):
                    quantities = property_set.Quantities

                    for qty in quantities:
                        if qty.is_a('IfcQuantityArea'):
                            return {
                                'quantity': qty.AreaValue,
                                'unit': 'm2'
                            }
                        elif qty.is_a('IfcQuantityVolume'):
                            return {
                                'quantity': qty.VolumeValue,
                                'unit': 'm3'
                            }
                        elif qty.is_a('IfcQuantityLength'):
                            return {
                                'quantity': qty.LengthValue,
                                'unit': 'm'
                            }
                        elif qty.is_a('IfcQuantityCount'):
                            return {
                                'quantity': qty.CountValue,
                                'unit': 'pcs'
                            }

        return None

    except Exception:
        return None
```

### 5.3 DWG Native Support

#### Task 2.3.1: DWG Parser Integration
**Priority:** HIGH | **Effort:** 6 hours

**New file to create:**
- `backend/app/services/extraction/dwg_extractor.py`

**Dependencies:**
```
# Option 1: ODA File Converter (external tool)
# Option 2: LibreDWG bindings
# Option 3: Cloud API service (Autodesk Forge)
```

**Implementation (using conversion approach):**
```python
import subprocess
import tempfile
import os
from pathlib import Path
from .dxf_extractor import extract_from_dxf

def extract_from_dwg(file_path: str) -> List[Dict]:
    """
    Extract materials from DWG by converting to DXF first
    Uses ODA File Converter or similar tool
    """
    try:
        # Create temp directory for conversion
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(file_path)
            output_path = Path(temp_dir) / f"{input_path.stem}.dxf"

            # Option 1: Use ODA File Converter (if installed)
            converter_result = convert_dwg_to_dxf(
                str(input_path),
                str(output_path)
            )

            if converter_result and output_path.exists():
                # Process converted DXF
                return extract_from_dxf(str(output_path))

            # Option 2: Use Autodesk Forge API
            # return extract_via_forge_api(file_path)

            return [{
                'material_name': 'DWG Processing Required',
                'quantity': 0,
                'unit': 'N/A',
                'confidence_score': 0.0,
                'notes': 'DWG file requires conversion. Please upload DXF version.'
            }]

    except Exception as e:
        logger.error(f"DWG extraction failed: {e}")
        return []

def convert_dwg_to_dxf(input_path: str, output_path: str) -> bool:
    """
    Convert DWG to DXF using ODA File Converter
    """
    oda_converter = os.getenv('ODA_CONVERTER_PATH', '/usr/bin/ODAFileConverter')

    if not os.path.exists(oda_converter):
        logger.warning("ODA File Converter not found")
        return False

    try:
        subprocess.run([
            oda_converter,
            os.path.dirname(input_path),
            os.path.dirname(output_path),
            'ACAD2018',
            'DXF',
            '0',
            '1'
        ], check=True, timeout=60)

        return True

    except subprocess.SubprocessError as e:
        logger.error(f"DWG conversion failed: {e}")
        return False
```

### 5.4 Accuracy Tracking & Validation

#### Task 2.4.1: Extraction Metrics System
**Priority:** HIGH | **Effort:** 4 hours

**New files to create:**
- `backend/app/models/extraction_metrics.py`
- `backend/app/services/metrics.py`

**Implementation:**
```python
# extraction_metrics.py
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from app.db.base import Base

class ExtractionMetrics(Base):
    __tablename__ = "extraction_metrics"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("project_plan.id"), nullable=False)

    # Processing metrics
    processing_time_seconds = Column(Float)
    pages_processed = Column(Integer)
    extraction_method = Column(String)  # 'pdf_text', 'pdf_vision', 'ifc', 'dxf'

    # Accuracy metrics
    materials_extracted = Column(Integer)
    avg_confidence_score = Column(Float)
    user_corrections = Column(Integer, default=0)
    accuracy_rating = Column(Float)  # User-provided

    # AI model info
    model_used = Column(String)
    tokens_used = Column(Integer)

    # Raw response for debugging
    raw_response = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

# metrics.py
from sqlalchemy.orm import Session
from app.models import ExtractionMetrics
import time

class MetricsTracker:
    def __init__(self, plan_id: int, db: Session):
        self.plan_id = plan_id
        self.db = db
        self.start_time = None
        self.metrics = {}

    def start(self):
        self.start_time = time.time()

    def record(self, **kwargs):
        self.metrics.update(kwargs)

    def finish(self):
        processing_time = time.time() - self.start_time

        metrics = ExtractionMetrics(
            plan_id=self.plan_id,
            processing_time_seconds=processing_time,
            **self.metrics
        )

        self.db.add(metrics)
        self.db.commit()

        return metrics

# Usage
tracker = MetricsTracker(plan_id, db)
tracker.start()
# ... extraction logic ...
tracker.record(
    pages_processed=5,
    extraction_method='pdf_vision',
    materials_extracted=len(materials),
    avg_confidence_score=sum(m['confidence_score'] for m in materials) / len(materials),
    model_used='gpt-4o',
    tokens_used=response.usage.total_tokens
)
tracker.finish()
```

---

## 6. Phase 3: Supply Chain & Weather

### 6.1 Real Weather API Integration

#### Task 3.1.1: Weather Service with Real API
**Priority:** HIGH | **Effort:** 4 hours

**Files to modify:**
- `backend/app/services/weather.py`
- `backend/app/core/config.py`

**Implementation:**
```python
# config.py additions
OPENWEATHER_API_KEY: Optional[str] = None
WEATHER_CACHE_TTL: int = 3600  # 1 hour

# weather.py
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Construction weather thresholds
CONSTRUCTION_THRESHOLDS = {
    'concrete_pour': {
        'min_temp': 5,   # Celsius
        'max_temp': 35,
        'max_wind': 40,  # km/h
        'no_rain': True,
        'min_humidity': 20,
        'max_humidity': 80
    },
    'roofing': {
        'min_temp': 0,
        'max_temp': 40,
        'max_wind': 50,
        'no_rain': True
    },
    'painting_exterior': {
        'min_temp': 10,
        'max_temp': 35,
        'no_rain': True,
        'min_humidity': 40,
        'max_humidity': 70
    },
    'excavation': {
        'max_rain': 10,  # mm
        'no_freeze': True
    },
    'general_construction': {
        'min_temp': -5,
        'max_temp': 40,
        'max_wind': 60,
        'max_rain': 25
    }
}

async def get_weather_forecast(
    location: str,
    days: int = 14
) -> Dict:
    """
    Get real weather forecast with construction suitability analysis
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("No weather API key, using mock data")
        return get_mock_weather(location)

    try:
        async with httpx.AsyncClient() as client:
            # Get coordinates first
            geo_response = await client.get(
                "http://api.openweathermap.org/geo/1.0/direct",
                params={
                    "q": location,
                    "limit": 1,
                    "appid": settings.OPENWEATHER_API_KEY
                }
            )
            geo_data = geo_response.json()

            if not geo_data:
                return {"error": "Location not found"}

            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']

            # Get forecast (free tier: 5-day, paid: 16-day)
            forecast_response = await client.get(
                "http://api.openweathermap.org/data/2.5/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric"
                }
            )
            forecast_data = forecast_response.json()

            # Process and analyze forecast
            processed_forecast = process_forecast(forecast_data)

            return {
                "location": location,
                "coordinates": {"lat": lat, "lon": lon},
                "forecast": processed_forecast,
                "construction_suitability": analyze_construction_suitability(processed_forecast)
            }

    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return get_mock_weather(location)

def analyze_construction_suitability(forecast: List[Dict]) -> List[Dict]:
    """
    Analyze each day for construction activity suitability
    """
    suitability = []

    for day in forecast:
        day_suitability = {
            "date": day["date"],
            "activities": {}
        }

        for activity, thresholds in CONSTRUCTION_THRESHOLDS.items():
            suitable = True
            reasons = []

            # Check temperature
            if 'min_temp' in thresholds and day['temp_min'] < thresholds['min_temp']:
                suitable = False
                reasons.append(f"Too cold ({day['temp_min']}°C)")

            if 'max_temp' in thresholds and day['temp_max'] > thresholds['max_temp']:
                suitable = False
                reasons.append(f"Too hot ({day['temp_max']}°C)")

            # Check wind
            if 'max_wind' in thresholds and day['wind_speed'] > thresholds['max_wind']:
                suitable = False
                reasons.append(f"Too windy ({day['wind_speed']} km/h)")

            # Check rain
            if thresholds.get('no_rain') and day['precipitation'] > 0:
                suitable = False
                reasons.append("Rain expected")

            day_suitability["activities"][activity] = {
                "suitable": suitable,
                "score": calculate_suitability_score(day, thresholds),
                "reasons": reasons if not suitable else ["Conditions favorable"]
            }

        suitability.append(day_suitability)

    return suitability
```

### 6.2 Real Supplier Integration

#### Task 3.2.1: Supplier API Integration Framework
**Priority:** HIGH | **Effort:** 8 hours

**New files to create:**
- `backend/app/services/suppliers/base.py`
- `backend/app/services/suppliers/api_integrations.py`
- `backend/app/models/supplier.py`

**Implementation:**
```python
# supplier.py model
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from app.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    api_type = Column(String)  # 'direct', 'marketplace', 'manual'
    api_endpoint = Column(String)
    api_credentials = Column(JSON)  # Encrypted in production

    # Categories
    material_categories = Column(JSON)  # ['concrete', 'steel', 'lumber']

    # Location
    country = Column(String)
    region = Column(String)
    delivery_radius_km = Column(Float)

    # Performance
    avg_delivery_days = Column(Float)
    reliability_score = Column(Float)  # 0-1
    quality_score = Column(Float)  # 0-1

    is_active = Column(Boolean, default=True)

# base.py - Abstract supplier interface
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class SupplierInterface(ABC):
    @abstractmethod
    async def get_pricing(
        self,
        material: str,
        quantity: float,
        unit: str
    ) -> Optional[Dict]:
        """Get pricing for a specific material"""
        pass

    @abstractmethod
    async def check_availability(
        self,
        material: str,
        quantity: float
    ) -> Dict:
        """Check material availability and lead time"""
        pass

    @abstractmethod
    async def get_delivery_estimate(
        self,
        material: str,
        quantity: float,
        destination: str
    ) -> Dict:
        """Get delivery time and cost estimate"""
        pass

# api_integrations.py
class SupplierAggregator:
    def __init__(self):
        self.suppliers: List[SupplierInterface] = []

    def register_supplier(self, supplier: SupplierInterface):
        self.suppliers.append(supplier)

    async def get_best_prices(
        self,
        materials: List[Dict],
        location: str
    ) -> List[Dict]:
        """
        Get best prices across all suppliers for a list of materials
        """
        recommendations = []

        for material in materials:
            best_option = None
            all_options = []

            for supplier in self.suppliers:
                try:
                    pricing = await supplier.get_pricing(
                        material['material_name'],
                        material['quantity'],
                        material['unit']
                    )

                    if pricing:
                        delivery = await supplier.get_delivery_estimate(
                            material['material_name'],
                            material['quantity'],
                            location
                        )

                        option = {
                            'supplier': supplier.name,
                            'unit_price': pricing['unit_price'],
                            'total_price': pricing['total_price'],
                            'delivery_days': delivery['days'],
                            'delivery_cost': delivery['cost'],
                            'availability': pricing['in_stock']
                        }

                        all_options.append(option)

                        if not best_option or option['total_price'] < best_option['total_price']:
                            best_option = option

                except Exception as e:
                    logger.error(f"Supplier {supplier.name} error: {e}")

            recommendations.append({
                'material': material['material_name'],
                'quantity': material['quantity'],
                'unit': material['unit'],
                'best_option': best_option,
                'all_options': sorted(all_options, key=lambda x: x['total_price'])
            })

        return recommendations
```

### 6.3 Inventory Management

#### Task 3.3.1: Inventory Tracking System
**Priority:** MEDIUM | **Effort:** 6 hours

**New files to create:**
- `backend/app/models/inventory.py`
- `backend/app/services/inventory.py`
- `backend/app/api/endpoints/inventory.py`

**Implementation:**
```python
# inventory.py model
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class InventoryStatus(enum.Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    ON_ORDER = "on_order"

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_plan.id"))

    material_name = Column(String, nullable=False, index=True)
    current_quantity = Column(Float, default=0)
    reserved_quantity = Column(Float, default=0)
    minimum_quantity = Column(Float)  # Reorder point
    unit = Column(String, nullable=False)

    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)

    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships
    movements = relationship("InventoryMovement", back_populates="inventory")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"))

    movement_type = Column(String)  # 'received', 'used', 'adjusted', 'returned'
    quantity = Column(Float, nullable=False)
    reference = Column(String)  # PO number, usage ticket, etc.
    notes = Column(String)

    created_by = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="movements")

# inventory.py service
class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def check_reorder_alerts(self, project_id: int) -> List[Dict]:
        """Check for materials below reorder point"""
        low_stock = self.db.query(Inventory).filter(
            Inventory.project_id == project_id,
            Inventory.current_quantity <= Inventory.minimum_quantity
        ).all()

        alerts = []
        for item in low_stock:
            alerts.append({
                'material': item.material_name,
                'current': item.current_quantity,
                'minimum': item.minimum_quantity,
                'needed': item.minimum_quantity - item.current_quantity,
                'status': 'CRITICAL' if item.current_quantity == 0 else 'LOW'
            })

        return alerts

    def record_usage(
        self,
        inventory_id: int,
        quantity: float,
        reference: str,
        user_id: int
    ) -> InventoryMovement:
        """Record material usage"""
        inventory = self.db.query(Inventory).get(inventory_id)

        if not inventory:
            raise ValueError("Inventory item not found")

        if inventory.current_quantity < quantity:
            raise ValueError("Insufficient inventory")

        # Create movement record
        movement = InventoryMovement(
            inventory_id=inventory_id,
            movement_type='used',
            quantity=-quantity,
            reference=reference,
            created_by=user_id
        )

        # Update inventory
        inventory.current_quantity -= quantity
        inventory.last_updated = datetime.utcnow()

        # Update status
        if inventory.current_quantity == 0:
            inventory.status = InventoryStatus.OUT_OF_STOCK
        elif inventory.current_quantity <= inventory.minimum_quantity:
            inventory.status = InventoryStatus.LOW_STOCK

        self.db.add(movement)
        self.db.commit()

        return movement
```

---

## 7. Phase 4: Dashboard & Analytics

### 7.1 KPI Dashboard

#### Task 4.1.1: Analytics Data Models
**Priority:** HIGH | **Effort:** 4 hours

**New file to create:**
- `backend/app/models/analytics.py`

**Implementation:**
```python
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from app.db.base import Base

class ProjectMetrics(Base):
    __tablename__ = "project_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_plan.id"))

    # Cost metrics
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    cost_variance = Column(Float)
    cost_variance_percent = Column(Float)

    # Material metrics
    estimated_materials_cost = Column(Float)
    actual_materials_cost = Column(Float)
    waste_percentage = Column(Float)
    waste_cost = Column(Float)

    # Time metrics
    planned_duration_days = Column(Integer)
    actual_duration_days = Column(Integer)
    weather_delay_days = Column(Integer)
    supply_delay_days = Column(Integer)

    # Quality metrics
    extraction_accuracy = Column(Float)
    prediction_accuracy = Column(Float)

    # Savings
    total_savings = Column(Float)
    optimization_savings = Column(Float)

    calculated_at = Column(DateTime, default=datetime.utcnow)

class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_plan.id"))
    snapshot_date = Column(DateTime, nullable=False)

    # Daily metrics
    materials_used = Column(JSON)  # [{material, quantity, cost}]
    waste_generated = Column(JSON)
    weather_impact = Column(String)  # 'none', 'minor', 'major', 'stopped'

    # Cumulative
    cumulative_cost = Column(Float)
    cumulative_waste_percent = Column(Float)
    progress_percent = Column(Float)
```

#### Task 4.1.2: Dashboard API Endpoints
**Priority:** HIGH | **Effort:** 4 hours

**New file to create:**
- `backend/app/api/endpoints/analytics.py`

**Implementation:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """Get summary metrics for user's projects"""

    # Get all user's projects
    projects = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.user_id == current_user.id
    ).all()

    total_estimated_savings = 0
    total_waste_reduction = 0
    active_projects = 0

    for project in projects:
        metrics = db.query(ProjectMetrics).filter(
            ProjectMetrics.project_id == project.id
        ).order_by(ProjectMetrics.calculated_at.desc()).first()

        if metrics:
            total_estimated_savings += metrics.total_savings or 0
            total_waste_reduction += metrics.waste_percentage or 0
            active_projects += 1

    avg_waste_reduction = total_waste_reduction / active_projects if active_projects > 0 else 0

    return {
        "total_projects": len(projects),
        "active_projects": active_projects,
        "total_estimated_savings": total_estimated_savings,
        "avg_waste_reduction_percent": avg_waste_reduction,
        "recent_activity": get_recent_activity(db, current_user.id)
    }

@router.get("/dashboard/project/{project_id}/metrics")
async def get_project_metrics(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """Get detailed metrics for a specific project"""

    # Verify ownership
    project = db.query(models.ProjectPlan).filter(
        models.ProjectPlan.id == project_id,
        models.ProjectPlan.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest metrics
    metrics = db.query(ProjectMetrics).filter(
        ProjectMetrics.project_id == project_id
    ).order_by(ProjectMetrics.calculated_at.desc()).first()

    # Get trend data (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    snapshots = db.query(DailySnapshot).filter(
        DailySnapshot.project_id == project_id,
        DailySnapshot.snapshot_date >= thirty_days_ago
    ).order_by(DailySnapshot.snapshot_date).all()

    return {
        "project": project,
        "current_metrics": metrics,
        "trend_data": [
            {
                "date": s.snapshot_date.isoformat(),
                "cost": s.cumulative_cost,
                "waste": s.cumulative_waste_percent,
                "progress": s.progress_percent
            }
            for s in snapshots
        ]
    }
```

### 7.2 Frontend Dashboard Components

#### Task 4.2.1: Dashboard Widgets
**Priority:** HIGH | **Effort:** 8 hours

**New files to create:**
- `frontend/src/components/dashboard/WasteMeter.tsx`
- `frontend/src/components/dashboard/CostTracker.tsx`
- `frontend/src/components/dashboard/MaterialStatus.tsx`
- `frontend/src/components/dashboard/WeatherPanel.tsx`
- `frontend/src/components/dashboard/TimelineView.tsx`

**WasteMeter Component:**
```typescript
'use client';

import React from 'react';
import { Box, Typography, CircularProgress, Card, CardContent } from '@mui/material';

interface WasteMeterProps {
    target: number;  // Target waste percentage
    actual: number;  // Actual waste percentage
    savings?: number; // Cost savings
}

export default function WasteMeter({ target, actual, savings }: WasteMeterProps) {
    const isOnTarget = actual <= target;
    const progress = Math.min((target / actual) * 100, 100);

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    מד בזבוז חומרים
                </Typography>

                <Box sx={{
                    position: 'relative',
                    display: 'flex',
                    justifyContent: 'center',
                    my: 2
                }}>
                    <CircularProgress
                        variant="determinate"
                        value={progress}
                        size={120}
                        thickness={8}
                        sx={{
                            color: isOnTarget ? 'success.main' : 'error.main',
                            '& .MuiCircularProgress-circle': {
                                strokeLinecap: 'round',
                            }
                        }}
                    />
                    <Box
                        sx={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            textAlign: 'center'
                        }}
                    >
                        <Typography variant="h4" color={isOnTarget ? 'success.main' : 'error.main'}>
                            {actual.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            יעד: {target}%
                        </Typography>
                    </Box>
                </Box>

                {savings && (
                    <Typography variant="body2" textAlign="center" color="success.main">
                        חיסכון משוער: ₪{savings.toLocaleString()}
                    </Typography>
                )}
            </CardContent>
        </Card>
    );
}
```

**CostTracker Component:**
```typescript
'use client';

import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface CostData {
    date: string;
    budget: number;
    actual: number;
    projected: number;
}

interface CostTrackerProps {
    data: CostData[];
    totalBudget: number;
    currentSpend: number;
}

export default function CostTracker({ data, totalBudget, currentSpend }: CostTrackerProps) {
    const budgetUtilization = (currentSpend / totalBudget) * 100;
    const isOverBudget = currentSpend > totalBudget;

    return (
        <Card>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    מעקב עלויות
                </Typography>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Box>
                        <Typography variant="caption" color="text.secondary">
                            תקציב כולל
                        </Typography>
                        <Typography variant="h5">
                            ₪{totalBudget.toLocaleString()}
                        </Typography>
                    </Box>
                    <Box textAlign="right">
                        <Typography variant="caption" color="text.secondary">
                            הוצאה נוכחית
                        </Typography>
                        <Typography
                            variant="h5"
                            color={isOverBudget ? 'error.main' : 'text.primary'}
                        >
                            ₪{currentSpend.toLocaleString()}
                        </Typography>
                    </Box>
                </Box>

                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="budget"
                            stroke="#1976d2"
                            name="תקציב מתוכנן"
                            strokeDasharray="5 5"
                        />
                        <Line
                            type="monotone"
                            dataKey="actual"
                            stroke="#2e7d32"
                            name="הוצאה בפועל"
                        />
                        <Line
                            type="monotone"
                            dataKey="projected"
                            stroke="#ed6c02"
                            name="צפי"
                            strokeDasharray="3 3"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
```

---

## 8. Phase 5: Security & Compliance

### 8.1 Multi-Factor Authentication

#### Task 5.1.1: MFA Implementation
**Priority:** HIGH | **Effort:** 8 hours

**New files to create:**
- `backend/app/services/mfa.py`
- `backend/app/api/endpoints/mfa.py`

**Dependencies:**
```
pyotp==2.9.0
qrcode==7.4.2
```

**Implementation:**
```python
# mfa.py
import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Optional, Tuple

class MFAService:
    def __init__(self, app_name: str = "ConstructionAI Pro"):
        self.app_name = app_name

    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()

    def generate_provisioning_uri(self, secret: str, user_email: str) -> str:
        """Generate the URI for authenticator app setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=self.app_name
        )

    def generate_qr_code(self, uri: str) -> str:
        """Generate QR code as base64 string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        return base64.b64encode(buffer.getvalue()).decode()

    def verify_token(self, secret: str, token: str) -> bool:
        """Verify a TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup codes for account recovery"""
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(count)]

# API endpoint
@router.post("/mfa/setup")
async def setup_mfa(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """Initialize MFA setup for user"""
    mfa_service = MFAService()

    # Generate new secret
    secret = mfa_service.generate_secret()

    # Generate QR code
    uri = mfa_service.generate_provisioning_uri(secret, current_user.email)
    qr_code = mfa_service.generate_qr_code(uri)

    # Store secret temporarily (not activated yet)
    current_user.mfa_secret_temp = secret
    db.commit()

    return {
        "qr_code": qr_code,
        "secret": secret,  # Allow manual entry
        "message": "Scan QR code with your authenticator app"
    }

@router.post("/mfa/verify")
async def verify_mfa_setup(
    token: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """Verify MFA token to complete setup"""
    mfa_service = MFAService()

    if not current_user.mfa_secret_temp:
        raise HTTPException(status_code=400, detail="MFA setup not initiated")

    if mfa_service.verify_token(current_user.mfa_secret_temp, token):
        # Activate MFA
        current_user.mfa_secret = current_user.mfa_secret_temp
        current_user.mfa_enabled = True
        current_user.mfa_secret_temp = None

        # Generate backup codes
        backup_codes = mfa_service.generate_backup_codes()
        current_user.mfa_backup_codes = backup_codes

        db.commit()

        return {
            "message": "MFA enabled successfully",
            "backup_codes": backup_codes
        }

    raise HTTPException(status_code=400, detail="Invalid token")
```

### 8.2 Role-Based Access Control

#### Task 5.2.1: RBAC Implementation
**Priority:** HIGH | **Effort:** 6 hours

**New files to create:**
- `backend/app/models/permissions.py`
- `backend/app/services/authorization.py`

**Implementation:**
```python
# permissions.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base import Base

# Many-to-many: users <-> roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
)

# Many-to-many: roles <-> permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permission.id'), primary_key=True)
)

class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    permissions = relationship("Permission", secondary=role_permissions, backref="roles")
    users = relationship("User", secondary=user_roles, backref="roles")

class Permission(Base):
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    resource = Column(String)  # 'plans', 'users', 'reports', etc.
    action = Column(String)    # 'create', 'read', 'update', 'delete'

# Default roles
DEFAULT_ROLES = [
    {
        'name': 'admin',
        'description': 'Full system access',
        'permissions': ['*']
    },
    {
        'name': 'project_manager',
        'description': 'Manage projects and view reports',
        'permissions': [
            'plans:create', 'plans:read', 'plans:update',
            'reports:read', 'inventory:read', 'inventory:update'
        ]
    },
    {
        'name': 'procurement',
        'description': 'Manage procurement and suppliers',
        'permissions': [
            'plans:read', 'suppliers:*', 'inventory:*', 'orders:*'
        ]
    },
    {
        'name': 'viewer',
        'description': 'Read-only access',
        'permissions': ['plans:read', 'reports:read']
    }
]

# authorization.py
from functools import wraps
from fastapi import HTTPException, status

def require_permission(permission: str):
    """Decorator to check user permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def has_permission(user, permission: str) -> bool:
    """Check if user has specific permission"""
    resource, action = permission.split(':')

    for role in user.roles:
        for perm in role.permissions:
            # Admin wildcard
            if perm.name == '*':
                return True

            # Resource wildcard (e.g., 'plans:*')
            if perm.resource == resource and perm.action == '*':
                return True

            # Exact match
            if perm.resource == resource and perm.action == action:
                return True

    return False

# Usage in endpoint
@router.delete("/plans/{plan_id}")
@require_permission("plans:delete")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    # Delete plan logic
    pass
```

### 8.3 Audit Logging

#### Task 5.3.1: Audit Trail Implementation
**Priority:** HIGH | **Effort:** 4 hours

**New files to create:**
- `backend/app/models/audit.py`
- `backend/app/services/audit.py`

**Implementation:**
```python
# audit.py model
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from app.db.base import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)

    # Who
    user_id = Column(Integer, ForeignKey("user.id"))
    user_email = Column(String)
    ip_address = Column(String)
    user_agent = Column(String)

    # What
    action = Column(String, nullable=False)  # 'create', 'read', 'update', 'delete', 'login', 'logout'
    resource_type = Column(String, nullable=False)  # 'plan', 'user', 'report', etc.
    resource_id = Column(String)

    # Details
    old_values = Column(JSON)
    new_values = Column(JSON)
    metadata = Column(JSON)

    # When
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Status
    status = Column(String, default='success')  # 'success', 'failed'
    error_message = Column(String)

# audit.py service
from fastapi import Request
from sqlalchemy.orm import Session

class AuditService:
    def __init__(self, db: Session, request: Request = None):
        self.db = db
        self.request = request

    def log(
        self,
        user_id: int,
        user_email: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        old_values: dict = None,
        new_values: dict = None,
        status: str = 'success',
        error_message: str = None
    ):
        """Create audit log entry"""
        log_entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            ip_address=self._get_client_ip(),
            user_agent=self._get_user_agent(),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            old_values=old_values,
            new_values=new_values,
            status=status,
            error_message=error_message
        )

        self.db.add(log_entry)
        self.db.commit()

        return log_entry

    def _get_client_ip(self) -> str:
        if not self.request:
            return None

        forwarded = self.request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        return self.request.client.host if self.request.client else None

    def _get_user_agent(self) -> str:
        if not self.request:
            return None
        return self.request.headers.get("User-Agent")

# Middleware for automatic auditing
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Log certain actions automatically
        if request.method in ['POST', 'PUT', 'DELETE']:
            # Get user from request state
            user = getattr(request.state, 'user', None)
            if user:
                # Create audit log
                pass

        return response
```

---

## 9. Phase 6: Integration & Export

### 9.1 ERP Integration Framework

#### Task 6.1.1: SAP Integration
**Priority:** MEDIUM | **Effort:** 12 hours

**New files to create:**
- `backend/app/integrations/sap/`
- `backend/app/integrations/sap/client.py`
- `backend/app/integrations/sap/mappers.py`

**Implementation:**
```python
# client.py
import httpx
from typing import Dict, List, Optional
from app.core.config import settings

class SAPClient:
    """
    SAP Business One / S4HANA Integration Client
    Uses SAP OData/REST APIs
    """

    def __init__(self):
        self.base_url = settings.SAP_BASE_URL
        self.company_db = settings.SAP_COMPANY_DB
        self.session_id = None

    async def login(self, username: str, password: str) -> bool:
        """Authenticate with SAP"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/b1s/v1/Login",
                json={
                    "CompanyDB": self.company_db,
                    "UserName": username,
                    "Password": password
                }
            )

            if response.status_code == 200:
                self.session_id = response.json().get("SessionId")
                return True
            return False

    async def create_purchase_order(self, order_data: Dict) -> Optional[str]:
        """Create purchase order in SAP"""
        headers = {"Cookie": f"B1SESSION={self.session_id}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/b1s/v1/PurchaseOrders",
                headers=headers,
                json=order_data
            )

            if response.status_code == 201:
                return response.json().get("DocEntry")
            return None

    async def get_inventory_levels(self, item_codes: List[str]) -> List[Dict]:
        """Get inventory levels from SAP"""
        headers = {"Cookie": f"B1SESSION={self.session_id}"}

        items = []
        async with httpx.AsyncClient() as client:
            for code in item_codes:
                response = await client.get(
                    f"{self.base_url}/b1s/v1/Items('{code}')",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    items.append({
                        "item_code": code,
                        "quantity_on_hand": data.get("QuantityOnStock"),
                        "quantity_ordered": data.get("QuantityOrderedFromVendors")
                    })

        return items

# mappers.py
class SAPDataMapper:
    """Map internal data structures to/from SAP format"""

    @staticmethod
    def material_to_sap_item(material: Dict) -> Dict:
        """Convert material to SAP item format"""
        return {
            "ItemCode": material.get("sku") or material.get("material_name"),
            "ItemName": material["material_name"],
            "Quantity": material["quantity"],
            "UnitPrice": material.get("unit_price", 0),
            "WarehouseCode": material.get("warehouse", "01")
        }

    @staticmethod
    def plan_to_sap_order(plan: Dict, materials: List[Dict]) -> Dict:
        """Convert plan materials to SAP purchase order"""
        return {
            "CardCode": plan.get("vendor_code", "V10000"),
            "DocDueDate": plan.get("delivery_date"),
            "Comments": f"ConstructionAI Pro - Plan #{plan['id']}",
            "DocumentLines": [
                SAPDataMapper.material_to_sap_item(m)
                for m in materials
            ]
        }
```

### 9.2 Advanced Export Formats

#### Task 6.2.1: Multi-Format Export Service
**Priority:** HIGH | **Effort:** 6 hours

**Files to modify:**
- `backend/app/api/endpoints/export.py`

**Implementation:**
```python
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
import pandas as pd
import json
from io import BytesIO, StringIO

router = APIRouter()

class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def to_excel(self, plan_id: int) -> BytesIO:
        """Export to Excel with multiple sheets"""
        materials = self._get_materials(plan_id)
        metrics = self._get_metrics(plan_id)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Materials sheet
            df_materials = pd.DataFrame(materials)
            df_materials.to_excel(
                writer,
                sheet_name='Materials',
                index=False
            )

            # Summary sheet
            df_summary = pd.DataFrame([{
                'Total Materials': len(materials),
                'Estimated Cost': sum(m.get('estimated_cost', 0) for m in materials),
                'Avg Confidence': sum(m['confidence_score'] for m in materials) / len(materials) if materials else 0
            }])
            df_summary.to_excel(
                writer,
                sheet_name='Summary',
                index=False
            )

        output.seek(0)
        return output

    def to_csv(self, plan_id: int) -> StringIO:
        """Export to CSV"""
        materials = self._get_materials(plan_id)
        df = pd.DataFrame(materials)

        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return output

    def to_json(self, plan_id: int) -> str:
        """Export to JSON"""
        materials = self._get_materials(plan_id)
        return json.dumps(materials, ensure_ascii=False, indent=2)

    def to_xml(self, plan_id: int) -> str:
        """Export to XML (for ERP integration)"""
        materials = self._get_materials(plan_id)

        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_parts.append('<MaterialList>')

        for mat in materials:
            xml_parts.append('  <Material>')
            xml_parts.append(f'    <Name>{mat["material_name"]}</Name>')
            xml_parts.append(f'    <Quantity>{mat["quantity"]}</Quantity>')
            xml_parts.append(f'    <Unit>{mat["unit"]}</Unit>')
            xml_parts.append(f'    <Confidence>{mat["confidence_score"]}</Confidence>')
            xml_parts.append('  </Material>')

        xml_parts.append('</MaterialList>')

        return '\n'.join(xml_parts)

@router.get("/plans/{plan_id}/export")
async def export_plan(
    plan_id: int,
    format: str = "excel",
    db: Session = Depends(deps.get_db),
):
    """Export plan data in various formats"""
    export_service = ExportService(db)

    if format == "excel":
        content = export_service.to_excel(plan_id)
        return StreamingResponse(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=BOQ_{plan_id}.xlsx"}
        )

    elif format == "csv":
        content = export_service.to_csv(plan_id)
        return Response(
            content.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=BOQ_{plan_id}.csv"}
        )

    elif format == "json":
        content = export_service.to_json(plan_id)
        return Response(
            content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=BOQ_{plan_id}.json"}
        )

    elif format == "xml":
        content = export_service.to_xml(plan_id)
        return Response(
            content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=BOQ_{plan_id}.xml"}
        )

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
```

---

## 10. Phase 7: Testing & Quality

### 10.1 Test Suite Structure

#### Task 7.1.1: Unit Tests
**Priority:** HIGH | **Effort:** 12 hours

**New directory structure:**
```
backend/tests/
├── __init__.py
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── test_extraction.py
│   ├── test_supply_chain.py
│   ├── test_weather.py
│   └── test_auth.py
├── integration/
│   ├── __init__.py
│   ├── test_api_plans.py
│   ├── test_api_auth.py
│   └── test_database.py
└── e2e/
    ├── __init__.py
    └── test_full_workflow.py
```

**conftest.py:**
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.api.deps import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def sample_pdf_file():
    """Create sample PDF for testing"""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Test Construction Plan")
    p.drawString(100, 700, "Concrete: 100 m3")
    p.drawString(100, 650, "Steel: 5000 kg")
    p.save()
    buffer.seek(0)

    return buffer
```

**test_extraction.py:**
```python
import pytest
from app.services.extraction.pdf_extractor import extract_from_pdf
from app.services.extraction.dxf_extractor import extract_from_dxf
from unittest.mock import patch, MagicMock

class TestPDFExtraction:
    def test_extract_empty_pdf_returns_empty_list(self, tmp_path):
        """Test that empty PDF returns empty list"""
        # Create empty PDF
        pdf_path = tmp_path / "empty.pdf"
        # ... create empty PDF ...

        result = extract_from_pdf(str(pdf_path))
        assert result == [] or len(result) == 0

    @patch('app.services.extraction.pdf_extractor.OpenAI')
    def test_extract_with_materials(self, mock_openai, tmp_path, sample_pdf_file):
        """Test extraction with mock OpenAI response"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='[{"material_name": "Concrete", "quantity": 100, "unit": "m3", "confidence_score": 0.9}]'))
        ]
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        # Save sample PDF
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(sample_pdf_file.read())

        result = extract_from_pdf(str(pdf_path))

        assert len(result) == 1
        assert result[0]['material_name'] == 'Concrete'
        assert result[0]['quantity'] == 100

    def test_merge_duplicate_materials(self):
        """Test that duplicate materials are merged correctly"""
        from app.services.extraction.pdf_extractor import merge_duplicate_materials

        materials = [
            {"material_name": "Concrete", "quantity": 50, "unit": "m3", "confidence_score": 0.8},
            {"material_name": "Concrete", "quantity": 30, "unit": "m3", "confidence_score": 0.9},
        ]

        result = merge_duplicate_materials(materials)

        assert len(result) == 1
        assert result[0]['quantity'] == 80
        assert result[0]['confidence_score'] == 0.85
```

### 10.2 Load Testing

#### Task 7.2.1: Performance Testing Setup
**Priority:** MEDIUM | **Effort:** 4 hours

**New file to create:**
- `tests/load/locustfile.py`

**Implementation:**
```python
from locust import HttpUser, task, between
import random

class ConstructionAIUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Login on start"""
        response = self.client.post("/login/access-token", data={
            "username": "test@example.com",
            "password": "testpassword"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(3)
    def view_dashboard(self):
        """View dashboard - most common action"""
        self.client.get("/plans/", headers=self.headers)

    @task(2)
    def view_plan_details(self):
        """View specific plan details"""
        plan_id = random.randint(1, 100)
        self.client.get(f"/plans/{plan_id}/quantities", headers=self.headers)
        self.client.get(f"/plans/{plan_id}/status", headers=self.headers)

    @task(1)
    def get_weather(self):
        """Get weather forecast"""
        locations = ["Tel Aviv", "Jerusalem", "Haifa", "Beer Sheva"]
        location = random.choice(locations)
        self.client.get(f"/optimization/weather?location={location}", headers=self.headers)

    @task(1)
    def upload_plan(self):
        """Upload a plan - resource intensive"""
        # Use small test file
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        self.client.post("/plans/upload", files=files, headers=self.headers)

# Run with:
# locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## 11. Phase 8: Mobile & Field App

### 11.1 React Native App Setup

#### Task 8.1.1: Mobile App Foundation
**Priority:** LOW | **Effort:** 16 hours

**New directory structure:**
```
mobile/
├── App.tsx
├── package.json
├── src/
│   ├── screens/
│   │   ├── LoginScreen.tsx
│   │   ├── DashboardScreen.tsx
│   │   ├── PlanDetailScreen.tsx
│   │   └── CameraScreen.tsx
│   ├── components/
│   │   ├── MaterialList.tsx
│   │   └── OfflineIndicator.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── offline.ts
│   └── store/
│       └── store.ts
└── ios/
└── android/
```

**package.json:**
```json
{
  "name": "constructionai-mobile",
  "version": "1.0.0",
  "main": "expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios"
  },
  "dependencies": {
    "expo": "~50.0.0",
    "react": "18.2.0",
    "react-native": "0.73.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/stack": "^6.3.0",
    "@reduxjs/toolkit": "^2.0.0",
    "react-redux": "^9.0.0",
    "axios": "^1.6.0",
    "@react-native-async-storage/async-storage": "^1.21.0",
    "expo-camera": "~14.0.0",
    "expo-file-system": "~16.0.0"
  }
}
```

---

## 12. Technical Implementation Details

### 12.1 Background Task Queue

**Implementation using Celery + Redis:**

```python
# backend/app/worker.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "constructionai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
)

@celery_app.task(bind=True)
def process_plan_task(self, plan_id: int):
    """Background task for plan processing"""
    from app.services.ai_engine import process_plan
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        # Update task progress
        self.update_state(state='PROCESSING', meta={'progress': 0})

        result = process_plan(plan_id, db)

        return {'status': 'completed', 'materials_count': len(result)}

    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
    finally:
        db.close()
```

### 12.2 WebSocket Real-time Updates

**Implementation:**

```python
# backend/app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, plan_id: int):
        await websocket.accept()
        if plan_id not in self.active_connections:
            self.active_connections[plan_id] = []
        self.active_connections[plan_id].append(websocket)

    def disconnect(self, websocket: WebSocket, plan_id: int):
        if plan_id in self.active_connections:
            self.active_connections[plan_id].remove(websocket)

    async def broadcast_progress(self, plan_id: int, progress: int, status: str):
        """Broadcast progress update to all connected clients"""
        if plan_id in self.active_connections:
            message = json.dumps({
                "type": "progress",
                "plan_id": plan_id,
                "progress": progress,
                "status": status
            })
            for connection in self.active_connections[plan_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/plans/{plan_id}")
async def websocket_endpoint(websocket: WebSocket, plan_id: int):
    await manager.connect(websocket, plan_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, plan_id)
```

---

## 13. Database Schema Evolution

### Full Schema Diagram (Target State)

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│        user         │     │       role          │     │     permission      │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │     │ id (PK)             │
│ email               │◄───┼│ name                │◄───┼│ name                │
│ full_name           │    ││ description         │    ││ resource            │
│ hashed_password     │    │└─────────────────────┘    ││ action              │
│ is_active           │    │                           │└─────────────────────┘
│ is_superuser        │    │                           │
│ mfa_enabled         │    │     user_roles            │    role_permissions
│ mfa_secret          │    │ ┌─────────────────┐       │ ┌─────────────────┐
│ created_at          │    │ │ user_id (FK)    │       │ │ role_id (FK)    │
│ updated_at          │    │ │ role_id (FK)    │       │ │ permission_id   │
└─────────────────────┘    │ └─────────────────┘       │ └─────────────────┘
         │                 │                           │
         │                 │                           │
         ▼                 │                           │
┌─────────────────────┐    │                           │
│    project_plan     │    │                           │
├─────────────────────┤    │                           │
│ id (PK)             │    │                           │
│ user_id (FK)        │◄───┘                           │
│ filename            │                                │
│ file_path           │                                │
│ file_type           │                                │
│ processing_status   │                                │
│ processing_progress │                                │
│ uploaded_at         │                                │
└─────────────────────┘                                │
         │                                             │
         │                                             │
         ▼                                             │
┌─────────────────────┐     ┌─────────────────────┐    │
│  material_quantity  │     │  extraction_metrics │    │
├─────────────────────┤     ├─────────────────────┤    │
│ id (PK)             │     │ id (PK)             │    │
│ plan_id (FK)        │     │ plan_id (FK)        │    │
│ material_name       │     │ processing_time     │    │
│ quantity            │     │ pages_processed     │    │
│ unit                │     │ extraction_method   │    │
│ confidence_score    │     │ materials_extracted │    │
│ source              │     │ avg_confidence      │    │
│ element_id          │     │ model_used          │    │
└─────────────────────┘     │ tokens_used         │    │
                            │ created_at          │    │
                            └─────────────────────┘    │
                                                       │
┌─────────────────────┐     ┌─────────────────────┐    │
│     inventory       │     │ inventory_movement  │    │
├─────────────────────┤     ├─────────────────────┤    │
│ id (PK)             │     │ id (PK)             │    │
│ project_id (FK)     │     │ inventory_id (FK)   │    │
│ material_name       │     │ movement_type       │    │
│ current_quantity    │     │ quantity            │    │
│ reserved_quantity   │     │ reference           │    │
│ minimum_quantity    │     │ created_by (FK)     │    │
│ unit                │     │ created_at          │    │
│ status              │     └─────────────────────┘    │
│ last_updated        │                                │
└─────────────────────┘                                │
                                                       │
┌─────────────────────┐     ┌─────────────────────┐    │
│     supplier        │     │    audit_log        │    │
├─────────────────────┤     ├─────────────────────┤    │
│ id (PK)             │     │ id (PK)             │    │
│ name                │     │ user_id (FK)        │◄───┘
│ api_type            │     │ user_email          │
│ api_endpoint        │     │ ip_address          │
│ api_credentials     │     │ action              │
│ material_categories │     │ resource_type       │
│ country             │     │ resource_id         │
│ region              │     │ old_values          │
│ delivery_radius_km  │     │ new_values          │
│ avg_delivery_days   │     │ timestamp           │
│ reliability_score   │     │ status              │
│ quality_score       │     └─────────────────────┘
│ is_active           │
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│   project_metrics   │     │   daily_snapshot    │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ project_id (FK)     │     │ project_id (FK)     │
│ estimated_cost      │     │ snapshot_date       │
│ actual_cost         │     │ materials_used      │
│ cost_variance       │     │ waste_generated     │
│ waste_percentage    │     │ weather_impact      │
│ planned_duration    │     │ cumulative_cost     │
│ actual_duration     │     │ cumulative_waste    │
│ weather_delay_days  │     │ progress_percent    │
│ total_savings       │     └─────────────────────┘
│ calculated_at       │
└─────────────────────┘
```

---

## 14. API Endpoints Roadmap

### Current Endpoints (Implemented)
```
Auth:
  POST /login/access-token     ✅ Implemented
  POST /register               ✅ Implemented

Plans:
  POST /plans/upload           ✅ Implemented
  GET  /plans/                 ✅ Implemented
  GET  /plans/{id}/quantities  ✅ Implemented
  GET  /plans/{id}/status      ✅ Implemented

Export:
  GET  /export/plans/{id}/excel ✅ Implemented

Optimization:
  POST /optimization/supply-chain ✅ Implemented (mock)
  GET  /optimization/weather      ✅ Implemented (mock)
```

### New Endpoints (To Be Implemented)

```
Auth (Phase 5):
  POST /mfa/setup              ⬜ MFA setup
  POST /mfa/verify             ⬜ MFA verification
  POST /mfa/disable            ⬜ Disable MFA

Plans (Phase 2):
  PUT  /plans/{id}             ⬜ Update plan
  DELETE /plans/{id}           ⬜ Delete plan
  POST /plans/{id}/reprocess   ⬜ Re-run extraction
  GET  /plans/{id}/versions    ⬜ Get version history

Materials (Phase 2):
  PUT  /plans/{id}/materials/{mat_id}  ⬜ Update material
  POST /plans/{id}/materials           ⬜ Add manual material
  DELETE /plans/{id}/materials/{mat_id} ⬜ Remove material

Inventory (Phase 3):
  GET  /inventory/                    ⬜ List inventory
  POST /inventory/                    ⬜ Add inventory item
  PUT  /inventory/{id}                ⬜ Update inventory
  POST /inventory/{id}/movement       ⬜ Record movement
  GET  /inventory/alerts              ⬜ Get low stock alerts

Suppliers (Phase 3):
  GET  /suppliers/                    ⬜ List suppliers
  POST /suppliers/                    ⬜ Add supplier
  GET  /suppliers/{id}/pricing        ⬜ Get pricing
  POST /suppliers/compare             ⬜ Compare suppliers

Analytics (Phase 4):
  GET  /analytics/dashboard           ⬜ Dashboard summary
  GET  /analytics/project/{id}        ⬜ Project metrics
  GET  /analytics/waste               ⬜ Waste analysis
  GET  /analytics/savings             ⬜ Savings report

Export (Phase 6):
  GET  /export/plans/{id}?format=csv  ⬜ CSV export
  GET  /export/plans/{id}?format=json ⬜ JSON export
  GET  /export/plans/{id}?format=xml  ⬜ XML export
  POST /export/erp/{system}           ⬜ ERP sync

Admin (Phase 5):
  GET  /admin/users                   ⬜ List users
  PUT  /admin/users/{id}/roles        ⬜ Assign roles
  GET  /admin/audit-logs              ⬜ View audit logs
  GET  /admin/system/health           ⬜ System health

WebSocket (Phase 4):
  WS  /ws/plans/{id}                  ⬜ Real-time updates
```

---

## 15. Frontend Component Library

### Component Hierarchy

```
src/
├── app/
│   ├── layout.tsx                    ✅ Exists
│   ├── page.tsx                      ✅ Exists
│   ├── (auth)/
│   │   ├── login/page.tsx            ✅ Exists
│   │   └── register/page.tsx         ✅ Exists
│   └── dashboard/
│       ├── page.tsx                  ✅ Exists
│       ├── analytics/page.tsx        ⬜ New
│       ├── inventory/page.tsx        ⬜ New
│       ├── suppliers/page.tsx        ⬜ New
│       ├── settings/page.tsx         ⬜ New
│       └── plans/
│           ├── [id]/page.tsx         ✅ Exists (needs fix)
│           └── [id]/edit/page.tsx    ⬜ New
├── components/
│   ├── common/
│   │   ├── LoadingSpinner.tsx        ⬜ New
│   │   ├── ErrorBoundary.tsx         ⬜ New
│   │   ├── ConfirmDialog.tsx         ⬜ New
│   │   └── DataTable.tsx             ⬜ New
│   ├── dashboard/
│   │   ├── WasteMeter.tsx            ⬜ New
│   │   ├── CostTracker.tsx           ⬜ New
│   │   ├── MaterialStatus.tsx        ⬜ New
│   │   ├── WeatherPanel.tsx          ⬜ New
│   │   └── TimelineView.tsx          ⬜ New
│   ├── plans/
│   │   ├── MaterialTable.tsx         ⬜ New (extract from page)
│   │   ├── MaterialEditor.tsx        ⬜ New
│   │   ├── VersionHistory.tsx        ⬜ New
│   │   └── ProcessingStatus.tsx      ⬜ New
│   ├── inventory/
│   │   ├── InventoryList.tsx         ⬜ New
│   │   ├── MovementForm.tsx          ⬜ New
│   │   └── AlertsPanel.tsx           ⬜ New
│   └── FileUpload.tsx                ✅ Exists
└── hooks/
    ├── useAuth.ts                    ⬜ New
    ├── usePlans.ts                   ⬜ New
    ├── useWebSocket.ts               ⬜ New
    └── useAnalytics.ts               ⬜ New
```

---

## 16. DevOps & Infrastructure

### 16.1 CI/CD Pipeline

**GitHub Actions Workflow:**

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run lint
        run: |
          cd frontend
          npm run lint

      - name: Run build
        run: |
          cd frontend
          npm run build

  deploy:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        run: |
          # Deployment steps here
          echo "Deploying to production..."
```

### 16.2 Docker Production Configuration

```yaml
# docker-compose.prod.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      SECRET_KEY: ${SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: always
    deploy:
      replicas: 2

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
```

---

## 17. Risk Mitigation

### 17.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI API rate limits | Medium | High | Implement caching, fallback models |
| BIM file parsing failures | High | Medium | Multiple parser fallbacks, manual upload option |
| Database performance degradation | Low | High | Connection pooling, query optimization, indexing |
| File storage capacity | Medium | Medium | Implement file cleanup, cloud storage migration |

### 17.2 Development Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | High | Strict sprint planning, MVP focus |
| Integration complexity | Medium | High | Incremental integration, mock services |
| Testing gaps | Medium | High | Test-driven development, CI/CD |
| Security vulnerabilities | Medium | Critical | Security audits, OWASP guidelines |

---

## Summary: Development Milestones

### Phase 1: Foundation (Weeks 1-2)
- [ ] Apply all critical bug fixes
- [ ] Setup Alembic migrations
- [ ] Configure logging
- [ ] Security hardening

### Phase 2: Core AI (Weeks 3-6)
- [ ] Enhanced PDF extraction
- [ ] BIM/IFC support
- [ ] DWG native support
- [ ] Accuracy metrics

### Phase 3: Supply Chain & Weather (Weeks 7-10)
- [ ] Real weather API
- [ ] Supplier integration framework
- [ ] Inventory management

### Phase 4: Dashboard & Analytics (Weeks 11-14)
- [ ] KPI dashboard
- [ ] Real-time updates
- [ ] Visualization components

### Phase 5: Security & Compliance (Weeks 15-18)
- [ ] MFA implementation
- [ ] RBAC system
- [ ] Audit logging
- [ ] Data encryption

### Phase 6: Integration & Export (Weeks 19-22)
- [ ] ERP integration framework
- [ ] Multi-format export
- [ ] API marketplace

### Phase 7: Testing & Quality (Weeks 23-24)
- [ ] Complete test suite
- [ ] Load testing
- [ ] Documentation

### Phase 8: Mobile App (Weeks 25-26)
- [ ] React Native setup
- [ ] Core mobile features
- [ ] Offline support

---

**Document prepared for ConstructionAI Pro development team.**
**Last updated: November 27, 2025**
