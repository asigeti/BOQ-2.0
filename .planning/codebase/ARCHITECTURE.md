# Architecture

**Analysis Date:** 2026-02-11

## Pattern Overview

**Overall:** Full-Stack Layered Monolith with AI Extraction Pipeline

**Key Characteristics:**
- Separate frontend (Next.js) and backend (FastAPI) services
- Multi-format document extraction pipeline (DWG, PDF, DXF, IFC)
- Multi-provider AI abstraction (Gemini, OpenAI, Claude, Ollama)
- Israeli construction domain (BOQ/כתב כמויות with Dekel pricing)
- Hebrew-first RTL interface throughout
- 4-level BOQ hierarchy (Sub-Document > Chapter > Sub-Chapter > Item)

## Layers

**Presentation Layer (Frontend):**
- Purpose: User interface with Hebrew RTL support
- Contains: Next.js App Router pages, React components, MUI theme
- Location: `frontend/src/app/`, `frontend/src/components/`
- Depends on: Backend REST API via Axios
- Used by: End users in browser

**API Gateway Layer:**
- Purpose: HTTP routing, CORS, authentication middleware
- Contains: FastAPI app setup, CORS config, JWT middleware
- Location: `backend/app/main.py`
- Depends on: Endpoint layer
- Used by: Frontend HTTP requests

**API Endpoints Layer:**
- Purpose: Route handlers, request validation, response formatting
- Contains: Auth, projects, plans, BOQ items, hierarchy, export endpoints
- Location: `backend/app/api/endpoints/`
- Depends on: Service layer, dependency injection (`backend/app/api/deps.py`)
- Used by: API Gateway

**Service Layer:**
- Purpose: Core business logic, extraction, BOQ generation, pricing
- Contains: AI engine, extractors, Israeli BOQ service, PDF generator
- Location: `backend/app/services/`
- Depends on: Data access layer, external AI APIs
- Used by: Endpoint handlers

**Data Access Layer:**
- Purpose: ORM models, Pydantic schemas, database session management
- Contains: SQLAlchemy models, Pydantic validation schemas
- Location: `backend/app/models/`, `backend/app/schemas/`, `backend/app/db/`
- Depends on: PostgreSQL database
- Used by: Service layer, Endpoint layer

**Persistence Layer:**
- Purpose: Data storage and caching
- Contains: PostgreSQL database, Redis cache, file system uploads
- Location: Docker containers, `uploads/` directory
- Used by: Data access layer

## Data Flow

**File Upload and Processing:**

1. User selects DWG/PDF file in FileUpload component (`frontend/src/components/FileUpload.tsx`)
2. FormData POST to `/projects/{id}/upload` via Axios
3. Backend saves file to `uploads/{project_id}/`, creates ProjectPlan record
4. BackgroundTask triggers `process_project_files()` (`backend/app/services/ai_engine.py`)
5. For DWG: AutoCAD COM / ezdxf extraction -> layer categorization -> status="extracted"
6. For PDF: Vision AI (Gemini -> OpenAI -> Claude fallback) -> status="extracted"
7. Frontend polls status, shows layer selection UI when extracted
8. User confirms layers -> POST triggers `generate_boq_for_plan()`
9. IsraeliBOQService generates 4-level hierarchy with Dekel pricing
10. Frontend displays AggregatedBOQView with hierarchical table

**API Request Lifecycle:**

1. HTTP request arrives at FastAPI
2. CORS middleware checks origin
3. Router matches URL to endpoint
4. Dependency injection: `get_db()` (session), `get_current_user()` (JWT)
5. Endpoint function validates input via Pydantic
6. Service layer executes business logic
7. Response serialized via Pydantic response model
8. JSON response returned

**State Management:**
- Frontend: Redux Toolkit for auth state (`frontend/src/store/slices/authSlice.ts`)
- Frontend: React Context for theme (`frontend/src/contexts/ThemeContext.tsx`)
- Backend: Stateless per-request (database for persistence)
- JWT token stored in localStorage (intercepted by Axios)

## Key Abstractions

**Extraction Pipeline:**
- Purpose: Multi-format document processing
- Examples: `backend/app/services/extraction/dwg_extractor.py`, `backend/app/services/extraction/pdf_extractor.py`
- Pattern: Strategy pattern with format-specific extractors + fallback chains

**Israeli BOQ Service:**
- Purpose: Domain-specific BOQ generation with Israeli standards
- Examples: `backend/app/services/boq/israeli_boq_service.py`
- Pattern: Domain service with construction type detection, chapter templates, Dekel pricing

**Multi-Provider AI:**
- Purpose: Abstraction over multiple LLM providers
- Examples: Gemini Vision, OpenAI GPT-4, Claude, Ollama (Aya + Qwen pipeline)
- Pattern: Strategy pattern with priority fallback (Gemini -> OpenAI -> Claude -> Ollama)

**4-Level BOQ Hierarchy:**
- Purpose: Israeli BOQ structure (תת כתב > פרק > תת פרק > סעיף)
- Examples: `backend/app/models/boq_hierarchy.py` (BOQSubDocument, BOQChapter, BOQSubChapter, BOQItem)
- Pattern: Composite tree with helper functions (`get_or_create_*`, `update_hierarchy_totals`)

**Layer Categorizer:**
- Purpose: Smart classification of CAD layers into include/exclude/review
- Examples: `backend/app/services/layer_categorizer.py`
- Pattern: Rule-based classification with pattern matching

## Entry Points

**Backend:**
- Location: `backend/app/main.py`
- Triggers: Uvicorn ASGI server on port 7000
- Responsibilities: Create FastAPI app, register CORS, include routers, create DB tables

**Frontend:**
- Location: `frontend/src/app/layout.tsx`
- Triggers: Next.js dev server on port 7001
- Responsibilities: HTML setup (lang="he" dir="rtl"), Provider tree initialization

**Provider Setup:**
- Location: `frontend/src/app/providers.tsx`
- Responsibilities: EmotionRegistry -> Redux Provider -> ThemeContextProvider -> NotificationProvider -> AuthHydrator

**Docker:**
- Location: `docker-compose.yml`
- Startup: PostgreSQL -> Redis -> Backend -> Frontend (dependency chain)

## Error Handling

**Strategy:** Exceptions at service layer, HTTPException at endpoint layer, try/catch at component level

**Patterns:**
- Backend services raise typed exceptions (ExtractionError, UnsupportedFileTypeError)
- Endpoints catch and convert to HTTPException with status codes
- Background tasks use try/except with logging and status updates
- Frontend uses try/catch with console.error (limited user notification)

## Cross-Cutting Concerns

**Logging:**
- Backend: Python `logging` module (no centralized config)
- Frontend: `console.error` (no structured logging)

**Validation:**
- Backend: Pydantic schemas at API boundary, SQLAlchemy constraints at DB level
- Frontend: TypeScript strict mode at compile time

**Authentication:**
- JWT tokens via python-jose, OAuth2 password bearer flow
- Token creation: `backend/app/core/security.py`
- Token validation: `backend/app/api/deps.py` (`get_current_user`)
- Note: Most endpoints lack auth checks currently (MVP)

**RTL/i18n:**
- Frontend: `stylis-plugin-rtl` for CSS, `lang="he" dir="rtl"` on HTML
- Backend: `arabic-reshaper` + `python-bidi` for PDF generation
- Font: Rubik (Hebrew-friendly)

---

*Architecture analysis: 2026-02-11*
*Update when major patterns change*
