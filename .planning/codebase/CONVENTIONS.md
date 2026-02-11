# Coding Conventions

**Analysis Date:** 2026-02-11

## Naming Patterns

**Files:**
- Backend: `snake_case.py` for all files (`boq_item.py`, `dwg_extractor.py`, `israeli_boq_service.py`)
- Frontend components: `PascalCase.tsx` (`FileUpload.tsx`, `AggregatedBOQView.tsx`, `MainLayout.tsx`)
- Frontend utilities: `camelCase.ts` (`axios.ts`, `authSlice.ts`)
- Frontend pages: `page.tsx` (Next.js App Router convention)

**Functions:**
- Backend: `snake_case` (`process_plan()`, `extract_raw_data_from_dwg()`, `categorize_layer()`)
- Frontend: `camelCase` (`handleSubmit`, `fetchProjects`, `setViewMode`)
- Event handlers: `handle{Event}` pattern (`handleClick`, `handleChange`, `handleFileUpload`)

**Variables:**
- Backend: `snake_case` (`project_id`, `selected_layers`, `file_extension`)
- Backend constants: `UPPER_SNAKE_CASE` (`LAYER_CATEGORIES`, `MAX_FILE_SIZE`, `SUPPORTED_EXTENSIONS`)
- Frontend: `camelCase` (`viewMode`, `processingProgress`, `isLoading`)
- Frontend constants: `UPPER_SNAKE_CASE` (`DRAWER_WIDTH`, `COLLAPSED_WIDTH`)

**Types:**
- Classes/Interfaces: `PascalCase` (`Project`, `BOQItem`, `AuthState`, `ProjectCreate`)
- No `I` prefix for interfaces
- Pydantic schemas: `PascalCase` with suffix (`ProjectCreate`, `BOQItemOut`, `BOQItemUpdate`)
- SQLAlchemy models: `PascalCase` matching table concept (`Project`, `BOQSubDocument`, `BOQChapter`)

## Code Style

**Formatting (Frontend):**
- 2 space indentation
- Single quotes for strings
- Semicolons required
- ~100 character line length (soft limit)
- ESLint with next/core-web-vitals (`frontend/eslint.config.mjs`)
- No Prettier configured

**Formatting (Backend):**
- 4 space indentation (PEP 8)
- Double quotes for docstrings, mixed for strings
- ~100 character line length (soft limit)
- No formatter configured (no Black, Ruff)

**Linting:**
- Frontend: ESLint 9 with eslint-config-next (`frontend/eslint.config.mjs`)
- Backend: No linter configured (no Ruff, Flake8, mypy)
- Run: `npm run lint` (frontend only)

## Import Organization

**Frontend Order:**
1. External packages (`react`, `next/navigation`, `@mui/material`)
2. Redux/state (`@/store/store`, `@/store/slices/authSlice`)
3. Local components (`@/components/layout/Header`)
4. Local utilities (`@/utils/axios`)
5. Types (`import type { Project }`)

**Frontend Path Aliases:**
- `@/*` maps to `./src/*` (`frontend/tsconfig.json`)

**Backend Order:**
1. Standard library (`os`, `json`, `datetime`, `typing`)
2. Third-party (`fastapi`, `sqlalchemy`, `pydantic`)
3. Local (`app.models`, `app.schemas`, `app.services`, `app.api.deps`)

**Backend Grouping:**
- Related imports together, blank lines between groups
- Inline imports used in background tasks to avoid circular dependencies

## Error Handling

**Backend Patterns:**
- Service layer raises typed exceptions (`ExtractionError`, `UnsupportedFileTypeError`)
- Endpoint layer catches and converts to `HTTPException` with status codes
- Background tasks use try/except with logging and status field updates
- Generic `Exception` catch with `traceback.format_exc()` logging

**Frontend Patterns:**
- try/catch around API calls with `axios.isAxiosError()` check
- `console.error` for logging (no structured error reporting)
- Limited user-facing error notifications

**Error Types:**
- Backend: `HTTPException(status_code=404, detail="Project not found")`
- Backend: `HTTPException(status_code=500, detail=f"Failed: {str(e)}")` (leaks details)
- Frontend: `catch (error: any)` (excessive `any` usage)

## Logging

**Framework:**
- Backend: Python `logging` module, no centralized config
- Frontend: `console.log` / `console.error`

**Patterns:**
- Backend uses `logger = logging.getLogger(__name__)` per module
- Log levels: `logger.info()`, `logger.error()`, `logger.warning()`
- Error logging includes traceback: `logger.error(traceback.format_exc())`
- No structured logging, no log rotation configured

## Comments

**When to Comment:**
- Module-level docstrings for major service files
- Function docstrings for key public functions (inconsistent)
- Inline TODO comments for known gaps
- Hebrew domain terms explained in comments

**Docstring Format (Backend):**
```python
def process_project_files(project_id: int):
    """
    Background task to EXTRACT data from all plan files in a project.

    FLOW by file type:
    - DWG/DXF: Extract layers -> User selects -> Generate BOQ
    - PDF: Extract with Vision AI -> Generate BOQ directly
    """
```

**TODO Comments:**
- Format: `# TODO: description` (no username)
- Example: `# TODO: In future, store raw_data to avoid re-extraction`

## Function Design

**Size:**
- Large functions common (some 100+ lines), especially in endpoint files
- Service files can be 1000+ lines (`projects.py` ~2000 lines)
- No strict size limit enforced

**Parameters:**
- Backend: Type-annotated, FastAPI `Depends()` for injection
- Frontend: Destructured props with TypeScript interfaces
- Backend uses `*` separator for keyword-only args in FastAPI endpoints

**Return Values:**
- Backend: Pydantic schemas or `Any` for flexible returns
- Frontend: JSX elements from components
- Backend uses `response_model=` for typed responses

## Module Design

**Backend Exports:**
- No barrel files (import directly from module)
- `__init__.py` mostly empty (package markers)

**Frontend Exports:**
- Default exports for page components
- Named exports for utility functions
- `layout/index.ts` barrel file for layout components
- Path aliases (`@/`) preferred over relative imports

## Type Annotations

**Backend:**
- Type hints on function signatures (inconsistent coverage)
- Pydantic models provide runtime validation
- `from typing import List, Optional, Any, Dict, Tuple` usage
- `Config: from_attributes = True` for ORM mode

**Frontend:**
- TypeScript strict mode enabled (`frontend/tsconfig.json`)
- Interface-based props for components
- Excessive `any` usage in error handlers and API responses
- Missing dedicated type definition files for API responses

---

*Convention analysis: 2026-02-11*
*Update when patterns change*
