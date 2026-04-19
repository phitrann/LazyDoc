## Plan: FastAPI Next.js Repo Research Tool

Build a submission-ready GitHub Repository Research Tool in a 4-6 hour window with FastAPI backend, Next.js frontend, Tailwind styling, and an in-memory TTL cache. Deliver the full required flow first (URL input -> Research action -> structured report with clear states), then add your prioritized bonus items in order.

**Steps**
1. Phase 1 - Bootstrap and contracts: scaffold backend/frontend/docs structure, initialize FastAPI + Next.js, and lock request/response/error contracts up front.
2. Phase 2 - Backend core: implement URL validation, GitHub client with timeout/retry/token fallback, analyzer service, in-memory TTL caching, and POST research endpoint with partial-response support.
3. Phase 3 - Frontend flow: implement landing form, API client, report page sections (overview, insights, activity, structure), and loading/error/partial states.
4. Phase 4 - UX polish: apply Tailwind hierarchy for scannability, mobile/desktop responsiveness, and accessibility smoke pass.
5. Phase 5 - Bonus features (in your chosen priority): license detection, security/risk observations, README summarization, AI-generated recommendations.
6. Phase 6 - Verification and packaging: backend tests, manual repository test matrix, README run instructions, design/trade-off notes, AI usage notes, and rubric-based final gap check.

**Dependencies and Parallelism**
1. Backend Phase 2 and Frontend Phase 3 can run in parallel after Phase 1 contracts are fixed.
2. Bonus features start only after core verification is passing.
3. Documentation starts in parallel once backend endpoint and report rendering are stable.

**Relevant files (existing anchors)**
1. [.github/copilot-instructions.md](.github/copilot-instructions.md) - enforce conventions, structure, and deliverables.
2. [.github/prompts/assignment-rubric-checklist.prompt.md](.github/prompts/assignment-rubric-checklist.prompt.md) - final scoring and gap triage.
3. [.github/agents/github-repo-research-exercise.agent.md](.github/agents/github-repo-research-exercise.agent.md) - orchestrator with handoffs.
4. [.github/agents/research-ui-polish.agent.md](.github/agents/research-ui-polish.agent.md) - UI/readability specialization.
5. [.github/agents/research-backend-resilience.agent.md](.github/agents/research-backend-resilience.agent.md) - backend resilience specialization.

**Verification**
1. Backend unit tests: URL parser, error mapping, analyzer transforms.
2. Backend integration tests: success, invalid URL, not found, rate-limited.
3. Manual testing on at least 5 public repos (small, large, active, stale).
4. Manual UI checks for loading/error/partial states and responsive behavior.
5. Accessibility smoke check: labeled input, semantic headings, keyboard navigation.
6. Rubric run before submission; resolve highest-impact gaps first.

**Decisions**
1. Included in MVP: FastAPI + Next.js + Tailwind, in-memory TTL cache, clear error taxonomy, partial-response handling.
2. Included optional priorities: license detection, security/risk observations, README summarization, AI recommendations.
3. Excluded from MVP: deep dependency graph parsing and persistent cache backend.
4. Assumption: public repositories are primary scope; private repos require token and permissions.
