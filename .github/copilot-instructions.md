# AutoDoc Workspace Instructions

This workspace builds a GitHub Repository Research Tool for a technical exercise.
Default stack is FastAPI backend and Next.js frontend.

## Project Goals
- Accept a public GitHub repository URL.
- Run research and produce a structured report.
- Prioritize readability, reliability, and clear insights.

## Required Folder Structure
Use and preserve this structure:

```text
.github/
  agents/
  prompts/
backend/
  app/
    api/
    core/
    services/
    schemas/
    utils/
  tests/
frontend/
  src/
    app/
    components/
    lib/
    styles/
  public/
docs/
```

## Coding Conventions

### General
- Use TypeScript in frontend code.
- Use Python 3.11+ with type hints in backend code.
- Keep functions small and focused.
- Prefer explicit error handling with user-facing messages.
- Avoid dead code and commented-out blocks.

### FastAPI Backend
- Organize routes under backend/app/api.
- Keep GitHub API calls in backend/app/services, not route handlers.
- Validate all request payloads with Pydantic schemas.
- Centralize configuration and environment access in backend/app/core.
- Add timeout and retry logic for external calls where appropriate.
- Return normalized response shapes that frontend can render directly.

### Next.js Frontend
- Use app router patterns under frontend/src/app.
- Keep UI components in frontend/src/components.
- Keep data clients and report transformers in frontend/src/lib.
- Provide loading, empty, and error states for each major view.
- Prefer semantic HTML and accessible labels.
- Keep report sections scannable with clear headings and metrics.

## Report Requirements
The rendered report must include:
- Repository overview: name, owner, description, stars, forks, last updated.
- Project insights: main languages, dependency overview, structure summary.
- Activity and health: recent commits/activity signal, contributor overview.

Optional enhancements when time permits:
- License detection.
- Security or risk observations.
- README summarization.
- AI-generated recommendations.

## Quality and Validation
- Validate repository URL format before submission.
- Handle GitHub not found and rate limit errors clearly.
- Add at least one integration-level validation path (happy path).
- Keep README run steps accurate for both backend and frontend.

## Delivery Notes
Include in docs or README:
- Design decisions and trade-offs.
- How AI tools were used.
- What would be improved with more time.
