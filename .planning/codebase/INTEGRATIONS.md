# External Integrations

**Analysis Date:** 2026-02-11

## APIs & External Services

**AI Vision - Google Gemini (PRIMARY):**
- Purpose: PDF plan analysis and extraction via Vision AI
- SDK/Client: `google-genai >= 1.32.0` (`backend/requirements.txt`)
- Auth: API key in `GEMINI_API_KEY` env var (`backend/app/core/config.py`)
- Model: `gemini-3-pro-preview` (multimodal) (`backend/app/core/config.py`)
- Usage: `backend/app/services/extraction/pdf_extractor.py`

**AI Vision - OpenAI (SECONDARY):**
- Purpose: BOQ generation and PDF extraction fallback
- SDK/Client: `openai >= 1.0.0` (`backend/requirements.txt`)
- Auth: API key in `OPENAI_API_KEY` env var (`backend/app/core/config.py`)
- Model: GPT-4 (configurable via `AI_PROVIDER`)
- Usage: `backend/app/services/ai_engine.py`, `backend/app/services/boq/israeli_boq_service.py`, `backend/app/services/ai_description_generator.py`

**AI Vision - Anthropic Claude (FALLBACK):**
- Purpose: PDF extraction fallback when Gemini and OpenAI unavailable
- SDK/Client: `anthropic >= 0.18.0` (`backend/requirements.txt`)
- Auth: API key in `ANTHROPIC_API_KEY` env var (`backend/app/core/config.py`)
- Usage: `backend/app/services/extraction/pdf_extractor.py`

**AI Local - Ollama (LOCAL PIPELINE):**
- Purpose: Local multi-model BOQ generation without cloud APIs
- Client: httpx HTTP client (`backend/app/services/boq/ollama_service.py`)
- Base URL: `OLLAMA_BASE_URL` (default: `http://localhost:11434`) (`backend/app/core/config.py`)
- Models:
  - Aya Expanse 32B (`OLLAMA_HEBREW_MODEL`) - Hebrew language specialist
  - Qwen 2.5 72B (`OLLAMA_REASONING_MODEL`) - Reasoning, 128k context
- Pipeline: Aya reads Hebrew -> Qwen analyzes/generates BOQ -> Aya translates back
- Timeout: 600 seconds (`OLLAMA_TIMEOUT`) (`backend/app/core/config.py`)
- Multi-model flag: `OLLAMA_USE_MULTI_MODEL: bool = True`

**AI Provider Priority:** Gemini -> OpenAI -> Claude -> Ollama

## Data Storage

**Databases:**
- PostgreSQL 15 - Primary data store (`docker-compose.yml`)
  - Connection: `DATABASE_URL` env var (`backend/app/core/config.py`)
  - Default: `postgresql://boq_user:boq_password@localhost:7432/boq_db`
  - Client: SQLAlchemy 2.0.23 with psycopg2-binary (`backend/requirements.txt`)
  - Session: `backend/app/db/session.py` (pool_pre_ping=True)
  - Tables: project, project_plan, boq_items, boq_sub_document, boq_chapter, boq_sub_chapter, user, material, extraction_layer, project_metrics

**Caching:**
- Redis 7 - Session/cache store (`docker-compose.yml`)
  - Connection: `REDIS_URL` env var (default: `redis://redis:6379`)
  - Client: redis 5.0.1 (`backend/requirements.txt`)
  - Port: 7379 (external) -> 6379 (internal)
  - Note: Configured but not heavily utilized currently

**File Storage:**
- Local filesystem - User uploads (`uploads/` directory)
  - Structure: `uploads/{project_id}/{filename}`
  - Types: DWG, DXF, PDF files
  - No cloud storage integration

**Migrations:**
- Tool: Alembic (`backend/alembic/`)
  - Migration files: `backend/alembic/versions/`
  - Note: Not actively used; `Base.metadata.create_all()` used instead (`backend/app/main.py`)

## Authentication & Identity

**Auth Provider:**
- Custom JWT implementation (no third-party auth)
  - Library: python-jose[cryptography] 3.3.0 (`backend/requirements.txt`)
  - Algorithm: HS256 (`backend/app/core/config.py`)
  - Token expiration: 10,080 minutes (7 days) (`backend/app/core/config.py`)
  - Secret: `SECRET_KEY` env var

**Password Hashing:**
- passlib[bcrypt] 1.7.4 (`backend/requirements.txt`)
- Implementation: `backend/app/core/security.py`

**Token Storage:**
- Frontend: localStorage (XSS-vulnerable)
- Injection: Axios request interceptor (`frontend/src/utils/axios.ts`)
- Header: `Authorization: Bearer {token}`

**OAuth Integrations:**
- None configured

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Analytics:**
- None

**Logs:**
- Backend: Python `logging` to stdout/stderr (no centralized config)
- Frontend: `console.log` / `console.error`
- No log aggregation service

## CI/CD & Deployment

**Hosting:**
- Docker Compose - Local/development deployment (`docker-compose.yml`)
  - 4 services: db (PostgreSQL), redis, backend (FastAPI), frontend (Next.js)
  - Volume: `postgres_data` for database persistence
  - Hot reload via bind mounts (development)

**CI Pipeline:**
- None configured (no GitHub Actions, no automated testing)

## Environment Configuration

**Development:**
- Required env vars: `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY` (or `GEMINI_API_KEY`), `AI_PROVIDER`
- Secrets location: `backend/.env` (gitignored, but currently committed)
- No `.env.example` template exists
- Docker Compose provides defaults for DB and Redis

**Production:**
- Not configured (development-only setup)
- All config hardcoded for localhost
- CORS origins hardcoded: `["http://localhost:7001", "http://localhost:7000", "http://localhost:7777"]`

## Document Processing Integrations

**CAD File Processing:**
- AutoCAD COM Interface (Windows only) - `pywin32 >= 306` (`backend/requirements.txt`)
  - Most accurate DWG extraction method
  - Requires AutoCAD installation
- ODA DWG to DXF Converter - External tool fallback
- ezdxf 1.1.3 - DXF parsing library (`backend/requirements.txt`)
- ifcopenshell 0.7.0 - BIM IFC models (`backend/requirements.txt`)

**PDF Processing:**
- pypdf 3.17.1 - PDF text extraction (`backend/requirements.txt`)
- pdf2image >= 1.16.3 - PDF page to image conversion (`backend/requirements.txt`)
  - Requires Poppler (`C:\poppler\poppler-25.11.0\Library\bin`)
- PyMuPDF (fitz) - Fallback PDF renderer (`backend/app/services/extraction/pdf_extractor.py`)
- Pillow 10.1.0 - Image processing (`backend/requirements.txt`)

**PDF Generation:**
- reportlab 4.0.7 - Professional BOQ PDF output (`backend/requirements.txt`)
- arabic-reshaper 3.0.0 - Hebrew/Arabic text reshaping (`backend/requirements.txt`)
- python-bidi 0.4.2 - Bidirectional text layout (`backend/requirements.txt`)

**Excel Export:**
- openpyxl 3.1.2 - Write .xlsx files (`backend/requirements.txt`)
- pandas 2.1.3 - Data manipulation before export (`backend/requirements.txt`)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-02-11*
*Update when adding/removing external services*
