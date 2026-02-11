# Technology Stack

**Analysis Date:** 2026-02-11

## Languages

**Primary:**
- TypeScript 5.x - All frontend application code (`frontend/tsconfig.json`)
- Python 3.11 - All backend application code (`backend/Dockerfile`)

**Secondary:**
- JavaScript - Build scripts, config files (`frontend/eslint.config.mjs`)
- CSS - Global styles (`frontend/src/app/globals.css`)

## Runtime

**Environment:**
- Node.js 18 Alpine - Frontend runtime (`frontend/Dockerfile`)
- Python 3.11-slim - Backend runtime (`backend/Dockerfile`)
- PostgreSQL 15 - Database (`docker-compose.yml`)
- Redis 7 - Cache/session store (`docker-compose.yml`)

**Package Manager:**
- npm - Frontend (`frontend/package.json`)
- pip - Backend (`backend/requirements.txt`, 29 packages)

**Ports:**
- Backend API: 7000 (internal 8000 mapped)
- Frontend: 7001 (internal 3000 mapped)
- PostgreSQL: 7432 (internal 5432 mapped)
- Redis: 7379 (internal 6379 mapped)

## Frameworks

**Core:**
- Next.js 16.0.3 - Frontend web framework (`frontend/package.json`)
- React 19.2.0 - UI library (`frontend/package.json`)
- FastAPI 0.104.1 - Backend API framework (`backend/requirements.txt`)
- SQLAlchemy 2.0.23 - ORM (`backend/requirements.txt`)
- Pydantic 2.5.0 - Data validation (`backend/requirements.txt`)

**UI:**
- Material-UI (MUI) 7.3.5 - Component library (`frontend/package.json`)
- Emotion 11.x - CSS-in-JS (`frontend/package.json`)
- Framer Motion 12.23.24 - Animations (`frontend/package.json`)
- Recharts 3.4.1 - Data visualization (`frontend/package.json`)

**State Management:**
- Redux Toolkit 2.10.1 + react-redux 9.2.0 (`frontend/package.json`)

**Testing:**
- None configured (no vitest, jest, pytest)

**Build/Dev:**
- Next.js built-in bundler (`frontend/package.json`)
- ESLint 9 + eslint-config-next (`frontend/package.json`)
- Uvicorn 0.24.0 - ASGI server (`backend/requirements.txt`)
- Docker Compose - Container orchestration (`docker-compose.yml`)

## Key Dependencies

**Critical (Frontend):**
- axios 1.13.2 - HTTP client (`frontend/src/utils/axios.ts`)
- react-dropzone 14.3.8 - File upload (`frontend/src/components/FileUpload.tsx`)
- stylis-plugin-rtl 2.1.1 - RTL support for Hebrew (`frontend/package.json`)

**Critical (Backend):**
- python-jose[cryptography] 3.3.0 - JWT authentication (`backend/requirements.txt`)
- passlib[bcrypt] 1.7.4 - Password hashing (`backend/requirements.txt`)
- psycopg2-binary 2.9.9 - PostgreSQL adapter (`backend/requirements.txt`)
- pydantic-settings 2.1.0 - Configuration management (`backend/requirements.txt`)

**AI/ML:**
- google-genai >= 1.32.0 - Gemini Vision AI (primary) (`backend/requirements.txt`)
- openai >= 1.0.0 - OpenAI GPT-4 (`backend/requirements.txt`)
- anthropic >= 0.18.0 - Claude (fallback) (`backend/requirements.txt`)
- httpx - Ollama local AI client (`backend/app/services/boq/ollama_service.py`)

**Document Processing:**
- ezdxf 1.1.3 - DXF/CAD parsing (`backend/requirements.txt`)
- ifcopenshell 0.7.0 - BIM IFC models (`backend/requirements.txt`)
- pypdf 3.17.1 - PDF text extraction (`backend/requirements.txt`)
- pdf2image >= 1.16.3 - PDF to image conversion (`backend/requirements.txt`)
- Pillow 10.1.0 - Image processing (`backend/requirements.txt`)
- pywin32 >= 306 - AutoCAD COM interface, Windows only (`backend/requirements.txt`)

**Export/Generation:**
- reportlab 4.0.7 - PDF generation (`backend/requirements.txt`)
- arabic-reshaper 3.0.0 - Hebrew/Arabic text reshaping (`backend/requirements.txt`)
- python-bidi 0.4.2 - Bidirectional text layout (`backend/requirements.txt`)
- openpyxl 3.1.2 - Excel export (`backend/requirements.txt`)
- pandas 2.1.3 - Data analysis/aggregation (`backend/requirements.txt`)

## Configuration

**Environment:**
- Backend: `.env` file via pydantic-settings (`backend/app/core/config.py`)
- Frontend: `NEXT_PUBLIC_API_URL` env var (`frontend/src/utils/axios.ts`)
- No `.env.example` file exists (gap)
- Key vars: DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, AI_PROVIDER

**Build:**
- `frontend/tsconfig.json` - TypeScript config (strict mode, ES2017 target, `@/*` path alias)
- `frontend/eslint.config.mjs` - ESLint with next/core-web-vitals
- `frontend/next.config.ts` - Next.js config (minimal)
- `docker-compose.yml` - 4-service orchestration (db, redis, backend, frontend)

## Platform Requirements

**Development:**
- Windows 11 (primary dev platform, AutoCAD COM requires Windows)
- Node.js 18+, Python 3.11+
- Docker/Docker Compose for database services
- Poppler for PDF rendering (`C:\poppler\poppler-25.11.0\Library\bin`)

**Production:**
- Docker Compose deployment (4 containers)
- PostgreSQL 15 with persistent volume
- Redis 7 for caching
- Windows required for AutoCAD COM DWG extraction (ezdxf fallback on Linux)

---

*Stack analysis: 2026-02-11*
*Update after major dependency changes*
