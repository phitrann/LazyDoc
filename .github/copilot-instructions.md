# Copilot Instructions for LazyDoc

This repository is a **GitHub Repository Research Tool** with a FastAPI backend and Next.js frontend.

## Build, test, and lint commands

Run from repo root unless noted.

| Task | Command |
|---|---|
| Backend install | `cd backend && pip install -r requirements.txt` |
| Backend dev server | `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Backend tests (all) | `pytest` |
| Backend single test file | `pytest backend/tests/test_api.py` |
| Backend single test case | `pytest backend/tests/test_api.py::test_documentation_endpoint_force_regenerate` |
| Frontend install | `cd frontend && npm install` |
| Frontend dev server | `cd frontend && npm run dev` |
| Frontend production build | `cd frontend && npm run build` |
| Frontend start | `cd frontend && npm run start` |

There are currently **no dedicated lint scripts** in `frontend/package.json` and no separate backend linter config in the repo.

## High-level architecture

1. UI flow:
   - `frontend/src/app/page.tsx` collects a GitHub URL and routes to `/report?repo=...`.
   - `frontend/src/app/report/ReportClient.tsx` calls `generateDocumentation()` from `frontend/src/lib/api.ts`.

2. Frontend-to-backend boundary:
   - Frontend calls Next API routes (`/api/documentation`, `/api/research`).
   - These are proxy handlers in `frontend/src/app/api/**/route.ts` that forward to FastAPI using `BACKEND_INTERNAL_URL`.

3. Backend API layer:
   - FastAPI mounts `/api/research` and `/api/documentation` via `backend/app/api/research.py` and `backend/app/api/documentation.py`.
   - Both parse/validate repository URLs through `backend/app/utils/url_validator.py`.

4. Service layer orchestration:
   - `RepoAnalyzer` (`backend/app/services/repo_analyzer.py`) fetches repo metadata/languages/commits/contributors/tree from `GitHubClient`, then normalizes overview/insights/activity/structure.
   - `DocumentationGenerator` (`backend/app/services/documentation_generator.py`) builds on analyzer output, fetches README, optionally uses local LLM + embeddings (`local_models.py`), and generates sections + markdown.
   - Dependency injection/singletons are in `backend/app/core/dependencies.py`; shared in-memory caching is `backend/app/core/cache.py`.

## Key conventions in this codebase

- **Keep route handlers thin**: URL parsing and response-envelope shaping in routes; GitHub calls and report logic stay in `services/`.
- **Normalized response envelopes**:
  - Success/partial: `{"status":"success|partial","data":...,"warnings":[]}`
  - Error: `{"status":"error","error_code":"...","message":"...","retry_after_seconds":...}`
- **Partial-success model is intentional**: analyzer/doc generator can degrade gracefully and return warnings instead of failing entire requests.
- **Canonical repo identity**: `parse_repository_url()` lowercases owner/repo and strips optional `.git`; use it instead of ad hoc parsing.
- **Shared cache behavior**:
  - Analyzer cache key: `owner/repo`
  - Documentation cache key: `docs:owner/repo`
  - `force_regenerate` bypasses documentation cache.
- **Contract mirroring matters**: backend schemas in `backend/app/schemas/response.py` and frontend types in `frontend/src/lib/types.ts` should stay in sync.
- **Folder structure is part of project constraints** and should be preserved:
  - backend routes in `backend/app/api`, services in `backend/app/services`, schemas in `backend/app/schemas`, shared config/deps/cache in `backend/app/core`
  - frontend app-router pages in `frontend/src/app`, components in `frontend/src/components`, data clients/types in `frontend/src/lib`
- **Report output expectations**: always preserve sections for overview, insights, activity/health, and structure; README summary/recommendations/risk observations are optional enhancements when model services are unavailable.
