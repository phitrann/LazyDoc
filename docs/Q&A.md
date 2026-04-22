# Interview Q&A

## Part 1: Cheat Sheet

### What is this project?
LazyDoc is a GitHub repository research tool that takes a public repository URL and produces a structured technical report with repository metrics, documentation-oriented AI insights, and heuristic code-health findings.

### Architecture in 30 seconds
The frontend is a Next.js app that handles the user experience, PAT input, and report rendering. The backend is a FastAPI service that validates GitHub URLs, fetches repository data, normalizes it, computes code-health signals, generates AI-backed documentation content, and returns a frontend-friendly report.

### Why FastAPI + Next.js?
FastAPI makes the backend data pipeline typed and easy to evolve, while Next.js is a fast way to build a polished report UI with simple proxy routes for demos. The split keeps ingestion/normalization concerns separate from the browser experience.

### How does caching work?
The backend uses an in-memory TTL cache. Cached entries are now separated by auth context:
- anonymous requests share one scope
- PAT-backed requests share another scope

That prevents authenticated requests from accidentally reusing anonymously cached GitHub results.

### How does PAT and rate-limit handling work?
The user can paste a GitHub PAT on the report page. The frontend forwards it as `X-GitHub-Token`, the backend uses it on a per-request basis, and the response surfaces GitHub rate-limit metadata so the UI can show remaining quota and reset timing.

### Where is AI used?
AI is used for README summarization, recommendations, and risk observations. The app also supports targeted regeneration of individual AI sections and falls back deterministically if model services are unavailable.

### How did you use AI during development?
I used AI as a structured accelerator rather than as a blind code generator. I took UI inspiration from DeepWiki, used aura.build to turn that direction into a `DESIGN.md` design-system document, then used Codex/Copilot planning workflows to break implementation into focused workstreams and specialized agents.

### Why add code health?
It goes beyond raw GitHub metadata and shows more thoughtful insight. Even a lightweight heuristic analyzer adds value by surfacing maintainability and architecture signals, which matches the exercise’s emphasis on meaningful insights rather than data dumps.

### Biggest trade-offs
- In-memory cache instead of persistent storage
- Heuristic code-health analysis instead of full static analysis
- Manifest detection instead of deep dependency parsing
- Local-model dependency for richer AI output, with fallback logic when unavailable

---

## Part 2: Deeper Walkthrough Q&A

### Q: Walk me through a request from the browser to the report output.
A: The user submits a GitHub URL from the landing or report page. The frontend sends the request to a Next.js proxy route rather than calling FastAPI directly from the browser. The proxy forwards the request, plus an optional GitHub PAT. FastAPI validates the URL, checks the scoped cache, calls GitHub if needed, normalizes repository data through `RepoAnalyzer`, computes code-health output, and then `DocumentationGenerator` adds README summary, recommendations, risks, sections, and markdown. The frontend then renders those normalized blocks into a report.

### Q: Why split the system into a Next.js frontend and a FastAPI backend instead of building one monolith?
A: The split keeps concerns clean. The frontend focuses on evaluator-facing experience, navigation, state transitions, and rendering. The backend focuses on validation, GitHub data collection, normalization, resilience, and AI orchestration. That separation made the API easier to test, made the report contract cleaner, and reduced the chance of UI concerns leaking into ingestion logic.

### Q: Why normalize the GitHub responses instead of sending raw API payloads through?
A: Raw GitHub payloads are noisy and frontend-unfriendly. Normalization lets the UI work with stable blocks like `overview`, `insights`, `activity`, `structure`, and `code_health`, which keeps rendering logic simpler and makes the API easier to reason about during review.

### Q: Why use a frontend proxy route instead of letting the browser call FastAPI directly?
A: The proxy improves developer experience and demo deployment. It gives the frontend one consistent API origin, keeps PAT forwarding under server control, and makes it easier to expose a single public port during a demo. It also keeps browser code simpler because the app can treat `/api/*` as its integration surface.

### Q: What were the most thoughtful system-design decisions in this project?
A: A few decisions mattered more than any individual feature. First, normalizing all GitHub data into report-ready blocks created a stable contract between backend and UI. Second, separating `RepoAnalyzer`, `DocumentationGenerator`, and `CodeHealthAnalyzer` kept the system composable instead of turning route handlers into large orchestration functions. Third, using partial-success responses and warnings prevented one failing upstream call from collapsing the entire report. Fourth, scoped caching by auth context fixed correctness without overcomplicating the cache model for a public-repo exercise.

### Q: Why did the cache keys need to change?
A: Initially, the analyzer and documentation cache only keyed by `owner/repo`. That created a correctness bug: if an anonymous request cached a repository first, a later PAT-backed request could receive the same anonymous result instead of making a new authenticated GitHub request. The fix was to scope cached results by auth context without ever storing the raw PAT in the key.

### Q: Why was targeted AI refresh incorrect before the fix?
A: The targeted regeneration path reused any cached base report even when `force_regenerate=true`. That meant the AI section would refresh against stale repository metadata. The fix was to rebuild the base report when force refresh is requested, then regenerate only the selected AI section while keeping the streaming semantics intact.

### Q: Why support targeted AI regeneration instead of regenerating the whole report every time?
A: It improves user experience and cost discipline. README summaries, recommendations, and risk observations are the most iteration-heavy parts of the report. Letting the user refresh only one of them preserves the rest of the report context, makes the interaction feel faster, and avoids unnecessary repeated work when only one AI-generated section needs refinement.

### Q: How does the code-health feature work today?
A: It scans a bounded subset of source files and uses heuristic rules to detect secrets, risky execution patterns, debug statements, TODO markers, and import-graph architecture signals. It then computes a score, grade, breakdown, and top findings. It is useful as an advisory layer, not a full security scanner.

### Q: Where is the code-health feature still heuristic?
A: It relies on regexes and lightweight import-graph construction rather than AST-level semantic analysis. It also samples a limited subset of files for responsiveness. So it is great for surfacing suspicious patterns and maintainability signals, but not for making absolute security claims.

### Q: Why did you keep the code-health analyzer heuristic instead of making it much deeper?
A: Because this was an exercise with a 4-6 hour expectation. A lightweight analyzer demonstrates thoughtfulness and bonus insight generation without turning the project into a static-analysis platform. It was the right balance between showing initiative and respecting scope.

### Q: What edge cases does the app handle?
A: It handles invalid GitHub URLs, missing repositories, GitHub rate limiting, timeouts, upstream availability problems, model fallbacks, and partial-success responses where some signals could not be fetched cleanly.

### Q: How does the UI reflect missing or uncertain data instead of hiding it?
A: The UI surfaces warnings, partial-success states, fallback messages, and explicit code-health confidence/severity labels. I wanted the report to feel honest and evaluator-friendly rather than overconfident. If a section is heuristic or fallback-generated, the interface should make that understandable instead of pretending every data point has the same certainty.

### Q: What performance considerations did you think about?
A: Several choices were intentionally performance-aware. The backend uses in-memory TTL caching and concurrent-request dedupe to avoid repeated GitHub calls. The code-health analyzer scans a bounded set of files rather than the entire repository tree. The report UI supports targeted AI regeneration rather than re-running all AI content every time. The landing page falls back cleanly when trending data cannot be fetched. These aren’t large-scale optimizations, but they are the right performance choices for an exercise-sized app.

### Q: Why sample the repository for code health instead of scanning every file?
A: Full scans can become expensive quickly, especially for larger repos or language ecosystems with many generated files. Sampling keeps the response time practical and still demonstrates the feature. For a production system, I would move this to an asynchronous job with stronger configurability and deeper analysis coverage.

### Q: What guided the UI design?
A: I wanted the UI to feel like a credible technical tool rather than a generic dashboard. I used DeepWiki as inspiration for density, hierarchy, and developer-facing polish, then converted those visual observations into a reusable `DESIGN.md` via aura.build. That gave me a concrete design-language reference instead of improvising UI decisions one component at a time.

### Q: How did you make sure the DeepWiki inspiration stayed responsible?
A: I used it as inspiration for information density, scannability, and tone, not as something to replicate mechanically. The actual implementation is tailored to the exercise: lighter visual treatment, report-focused sections, and a structure aligned to the assignment rather than DeepWiki’s full product scope.

### Q: How did AI help beyond code generation?
A: It helped with design-system extraction, structured planning, and task decomposition. The useful part was not “write everything for me,” but “help me externalize good decisions faster.” I used AI to turn rough intent into concrete implementation plans, then validated and refined the result against the exercise rubric and the actual codebase.

### Q: What was the workflow with specialized agents?
A: I split the work into a main delivery agent plus focused specialists:
- `GitHub Repo Research Exercise Builder` for overall exercise execution and integration
- `Research Backend Resilience Specialist` for caching, normalization, and API robustness
- `Research UI Polish Specialist` for hierarchy, readability, and evaluator-facing UX polish

That decomposition matched the real concerns in the project and reduced the risk of solving everything through one generic pass.

### Q: Why was that multi-agent workflow useful here?
A: It encouraged sharper decision boundaries. Backend resilience decisions and UI readability decisions have different quality bars and trade-offs. By framing them as specialist concerns, I could reason about each area more clearly while still integrating them into one coherent submission.

### Q: How did plan mode change the outcome?
A: Plan mode was useful because it forced the implementation to be decision-complete before code changes started. That mattered for this project because there were trade-offs around caching, PAT handling, UI flow, and documentation scope. Planning first reduced churn and made the later implementation passes more cohesive.

### Q: How does the project map back to the exercise rubric?
A: It covers the core requirements with a clear report UI and normalized repository insights. It also covers several bonus items: README summarization, AI-generated insights, license detection, risk observations, PAT support, rate-limit visibility, and code-health signals. Structurally, it also demonstrates deliberate architecture, handling of edge cases, and a thoughtful use of AI tools.

### Q: If an interviewer asks where the “thoughtful design decisions” show up most clearly, what would you point to?
A: I would point to four places:
1. The normalized backend contract instead of raw GitHub payloads.
2. The scoped cache model that distinguishes anonymous and PAT-backed requests.
3. The honest UI treatment of partial or heuristic results.
4. The deliberate use of AI for planning, design extraction, and specialized implementation workflows rather than only code autocomplete.

### Q: What are the most important UI improvements you would make next?
A: I would focus on evaluator comprehension first:
- add provenance badges so users can distinguish GitHub-derived, AI-generated, and heuristic sections at a glance
- add a compact “report summary ribbon” near the top with stars, health grade, commit activity, and main risk
- improve mobile behavior for the code-health findings so they feel less dense
- add lightweight empty-state guidance for repos with sparse README or activity data
- give the markdown section a view toggle between rendered and raw markdown for faster reuse

### Q: What would you improve first for the exercise itself?
A: I would add a single end-to-end smoke test for the happy path, improve dependency insight depth by reading common manifest contents, sharpen provenance messaging in the UI, and automate screenshot capture as part of the submission refresh workflow.

### Q: What would you improve first for production readiness?
A: I would move caching to Redis, add background jobs for heavier analysis, version the analyzers so findings are explainable over time, and deepen code-health analysis with AST-aware rules, suppressions, and telemetry.

### Q: Why keep recommendations balanced between exercise polish and production hardening?
A: Because the project is being evaluated as an exercise today, but interviewers often want to hear both: what you intentionally scoped for the exercise and how you would evolve it responsibly if it became a real product. Showing both makes the trade-offs explicit.
