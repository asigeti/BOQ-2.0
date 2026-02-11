# Testing Patterns

**Analysis Date:** 2026-02-11

## Test Framework

**Runner:**
- None configured (no vitest, jest, pytest installed)

**Assertion Library:**
- None

**Run Commands:**
```bash
# No test commands available
# frontend: no test script in package.json
# backend: no pytest.ini or pyproject.toml
```

## Test File Organization

**Location:**
- No organized test structure exists
- Ad-hoc test scripts scattered at root and backend level

**Existing Ad-Hoc Scripts (NOT in test suite):**
- `test_autocad_com.py` - Root level, AutoCAD COM testing
- `backend/test_image_extraction.py` - Image extraction testing
- `backend/verify_openai.py` - OpenAI API verification
- `backend/create_boq_table.py` - Database table creation
- `backend/run_hierarchy_migration.py` - Migration runner
- Various debug scripts: `analyze_comparison.py`, `check_backend_health.py`, `compare_pdfs.py`, `debug_extraction_perf.py`

**Structure:**
```
# Current (no test infrastructure)
backend/
  test_image_extraction.py     # Ad-hoc, not in suite
  verify_openai.py             # Ad-hoc, not in suite
test_autocad_com.py            # Root level ad-hoc
```

## Test Structure

**Suite Organization:**
- Not applicable (no test suite)

**Patterns:**
- Not applicable

## Mocking

**Framework:**
- Not applicable (no mocking infrastructure)

## Fixtures and Factories

**Test Data:**
- No fixtures or factories defined
- Ad-hoc scripts create test data inline

## Coverage

**Requirements:**
- No coverage tracking
- No coverage targets
- 0% measured coverage

## Test Types

**Unit Tests:**
- None

**Integration Tests:**
- None

**E2E Tests:**
- None

## Current Code Quality Measures (Without Tests)

**TypeScript (Frontend):**
- Strict mode enabled in `frontend/tsconfig.json`
- Catches type errors at compile time
- Missing required props caught before runtime

**Pydantic (Backend):**
- Request validation at API boundary
- Invalid data types caught with 422 responses
- Schema-level field validation

**ESLint (Frontend):**
- next/core-web-vitals preset
- Catches common React mistakes, unused vars

**FastAPI OpenAPI:**
- Automatic API documentation (when enabled)
- Request/response schema validation

## What's NOT Prevented Without Tests

- Logic errors (valid data producing wrong results)
- Integration issues (frontend/backend communication)
- Business rule violations (incorrect BOQ generation)
- Performance regressions
- Data corruption (race conditions, cascade errors)
- User workflow failures

## Recommended Setup

**Backend (Priority: CRITICAL):**
```bash
# Install
pip install pytest pytest-cov pytest-asyncio httpx

# Structure
backend/
├── pytest.ini
├── conftest.py              # DB fixtures, test client
└── tests/
    ├── test_api/
    │   ├── test_projects.py
    │   ├── test_auth.py
    │   └── test_boq.py
    └── test_services/
        ├── test_dwg_extractor.py
        └── test_dekel_pricing.py
```

**Frontend (Priority: CRITICAL):**
```bash
# Install
npm install -D vitest @vitest/ui @testing-library/react jsdom

# Structure
frontend/
├── vitest.config.ts
└── src/
    ├── components/
    │   ├── FileUpload.test.tsx
    │   └── AggregatedBOQView.test.tsx
    └── store/slices/
        └── authSlice.test.ts
```

**Coverage Targets:**
- Backend services: 80%+
- Backend endpoints: 70%+
- Frontend components: 70%+
- Frontend store: 90%+

---

*Testing analysis: 2026-02-11*
*Update when test patterns change*
