# Codebase Structure

**Analysis Date:** 2026-02-11

## Directory Layout

```
BOQ-2.0/
├── backend/                    # FastAPI backend service
│   ├── app/                    # Main application code
│   │   ├── api/                # HTTP API layer
│   │   │   ├── endpoints/      # Route handlers
│   │   │   ├── api.py          # Router aggregation
│   │   │   └── deps.py         # Dependency injection
│   │   ├── core/               # Configuration & security
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   └── security.py     # JWT & password hashing
│   │   ├── db/                 # Database setup
│   │   │   ├── base.py         # SQLAlchemy declarative base
│   │   │   └── session.py      # Session factory
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/           # Business logic
│   │   │   ├── boq/            # BOQ generation services
│   │   │   ├── extraction/     # File format extractors
│   │   │   └── pricing/        # Dekel pricing services
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # Database migrations
│   │   └── versions/           # Migration scripts
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container
│   └── .env                    # Environment variables (gitignored)
├── frontend/                   # Next.js frontend service
│   ├── src/                    # Source code
│   │   ├── app/                # Next.js App Router
│   │   │   ├── (auth)/         # Auth route group (login, register)
│   │   │   ├── dashboard/      # Protected dashboard routes
│   │   │   ├── layout.tsx      # Root layout (RTL config)
│   │   │   ├── providers.tsx   # Provider tree setup
│   │   │   └── globals.css     # Global styles
│   │   ├── components/         # Reusable React components
│   │   │   └── layout/         # Layout components
│   │   ├── contexts/           # React Context providers
│   │   ├── store/              # Redux state management
│   │   │   └── slices/         # Redux slices
│   │   ├── theme/              # MUI theme configuration
│   │   └── utils/              # Utility functions
│   ├── public/                 # Static assets
│   ├── package.json            # Dependencies & scripts
│   ├── tsconfig.json           # TypeScript configuration
│   └── Dockerfile              # Frontend container
├── docs/                       # Project documentation
├── experts/                    # Expert persona definitions
├── .planning/                  # GSD framework planning
├── uploads/                    # User-uploaded files (runtime)
├── docker-compose.yml          # Container orchestration
├── CLAUDE.md                   # Project instructions
└── PRD.md                      # Product requirements
```

## Directory Purposes

**backend/app/api/endpoints/:**
- Purpose: FastAPI route handlers for all API endpoints
- Contains: `auth.py`, `projects.py`, `plans.py`, `boq_items.py`, `boq_hierarchy.py`, `export.py`, `optimization.py`
- Key files: `projects.py` (~2000 lines, largest endpoint file)

**backend/app/models/:**
- Purpose: SQLAlchemy ORM model definitions
- Contains: `project.py`, `plan.py`, `boq_item.py`, `boq_hierarchy.py`, `user.py`, `material.py`, `extraction_layer.py`, `metrics.py`
- Key files: `boq_hierarchy.py` (270 lines, 4-level hierarchy with helper functions)

**backend/app/services/:**
- Purpose: Core business logic layer
- Contains: AI engine, extractors, BOQ generation, PDF generation, pricing
- Key files: `ai_engine.py` (extraction orchestration), `pdf_generator.py` (PDF export)

**backend/app/services/extraction/:**
- Purpose: Multi-format document extraction
- Contains: `dwg_extractor.py` (1400+ lines), `pdf_extractor.py` (2700+ lines), `dxf_extractor.py`, `ifc_extractor.py`
- Key files: `pdf_extractor.py` (Vision AI integration with Gemini/OpenAI/Claude)

**backend/app/services/boq/:**
- Purpose: Israeli BOQ generation with domain logic
- Contains: `israeli_boq_service.py` (1800+ lines), `ollama_service.py`
- Key files: `israeli_boq_service.py` (Blue Book standards, Dekel pricing)

**frontend/src/app/:**
- Purpose: Next.js App Router pages (file-based routing)
- Contains: Layout, providers, auth pages, dashboard pages
- Subdirectories: `(auth)/` (login, register), `dashboard/` (main app)

**frontend/src/components/:**
- Purpose: Reusable React components
- Contains: `FileUpload.tsx`, `FileReviewStage.tsx`, `ExtractionReview.tsx`, `AggregatedBOQView.tsx`
- Subdirectories: `layout/` (MainLayout, Header, Sidebar)

**frontend/src/store/:**
- Purpose: Redux Toolkit state management
- Contains: `store.ts` (config), `slices/authSlice.ts` (auth state)

## Key File Locations

**Entry Points:**
- `backend/app/main.py` - FastAPI app creation, CORS, router inclusion
- `frontend/src/app/layout.tsx` - Root HTML layout (RTL, fonts)
- `frontend/src/app/providers.tsx` - Provider tree (Redux, Theme, Auth)
- `docker-compose.yml` - Multi-container orchestration

**Configuration:**
- `backend/app/core/config.py` - Settings class (env vars, AI keys, DB URL)
- `backend/app/core/security.py` - JWT creation, password hashing
- `frontend/tsconfig.json` - TypeScript config (strict, `@/*` alias)
- `frontend/src/theme/theme.ts` - MUI theme (dark/light, RTL, Hebrew fonts)
- `frontend/src/utils/axios.ts` - HTTP client with JWT interceptor

**Core Logic:**
- `backend/app/services/ai_engine.py` - Extraction orchestration
- `backend/app/services/extraction/dwg_extractor.py` - CAD extraction
- `backend/app/services/extraction/pdf_extractor.py` - Vision AI extraction
- `backend/app/services/boq/israeli_boq_service.py` - BOQ generation
- `backend/app/services/pricing/dekel_pricing.py` - Price lookup
- `backend/app/services/layer_categorizer.py` - Layer classification
- `backend/app/services/pdf_generator.py` - PDF export

**Testing:**
- No test framework configured
- Ad-hoc scripts at root: `test_autocad_com.py`, `verify_openai.py`
- Ad-hoc backend scripts: `backend/test_image_extraction.py`

**Documentation:**
- `CLAUDE.md` - Project instructions for Claude
- `PRD.md` - Product requirements
- `docs/ISRAELI_BOQ_KNOWLEDGE_BASE.md` - Domain reference
- `docs/EXPERT_CODE_REVIEW_REPORT.md` - Review findings

## Naming Conventions

**Files:**
- Backend: `snake_case.py` for all Python files (e.g., `boq_item.py`, `dwg_extractor.py`)
- Frontend components: `PascalCase.tsx` (e.g., `FileUpload.tsx`, `MainLayout.tsx`)
- Frontend utilities: `camelCase.ts` (e.g., `axios.ts`)
- Frontend pages: `page.tsx` (Next.js convention)
- Frontend slices: `camelCase.ts` (e.g., `authSlice.ts`)

**Directories:**
- Backend: `snake_case` for all directories
- Frontend: `kebab-case` or `camelCase` (e.g., `layout/`, `store/`)
- Next.js route groups: `(groupName)/` (e.g., `(auth)/`)
- Dynamic routes: `[param]/` (e.g., `[id]/`)

**Special Patterns:**
- `__init__.py` for Python package markers
- `UPPERCASE.md` for important project files (CLAUDE.md, PRD.md)

## Where to Add New Code

**New API Endpoint:**
- Implementation: `backend/app/api/endpoints/{resource}.py`
- Router registration: `backend/app/api/api.py`
- Schema: `backend/app/schemas/{resource}.py`
- Model (if needed): `backend/app/models/{resource}.py`

**New Service:**
- Implementation: `backend/app/services/{service_name}.py`
- Subdirectory for grouped services: `backend/app/services/{domain}/`

**New Frontend Page:**
- Implementation: `frontend/src/app/dashboard/{route}/page.tsx`

**New React Component:**
- Implementation: `frontend/src/components/{ComponentName}.tsx`
- Layout component: `frontend/src/components/layout/{ComponentName}.tsx`

**New Redux State:**
- Slice: `frontend/src/store/slices/{name}Slice.ts`
- Register in: `frontend/src/store/store.ts`

## Special Directories

**uploads/:**
- Purpose: User-uploaded plan files (DWG, PDF, DXF)
- Source: Created at runtime by file upload endpoint
- Committed: No (runtime data)

**alembic/versions/:**
- Purpose: Database migration scripts
- Source: Generated by Alembic
- Committed: Yes
- Note: Migrations exist but `Base.metadata.create_all()` is used instead

**.planning/:**
- Purpose: GSD framework planning documents
- Source: Generated by GSD commands
- Committed: Yes

---

*Structure analysis: 2026-02-11*
*Update when directory structure changes*
