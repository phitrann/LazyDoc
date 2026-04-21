# Code Health Roadmap

## 1. Current Status

LazyDoc already ships a lightweight code-health feature. It is no longer a proposal-only item.

Today the application produces a `code_health` block that includes:
- score and letter grade
- summary
- metric breakdown
- finding list
- security, architecture, and maintenance counts
- circular dependency and coupling signals

### Current implemented heuristics

#### Security-oriented checks
- Hardcoded secret/API-key pattern detection
- Suspicious credential literal detection
- Dynamic execution detection
- Shell execution detection

#### Maintenance-oriented checks
- Debug statement detection
- TODO / FIXME / XXX marker detection

#### Architecture-oriented checks
- Internal import graph extraction
- Coupling index
- Circular dependency detection
- Orphan-file density signal

### Current import-resolution support

For Python files, the analyzer now resolves:
- absolute imports such as `from app.utils import url_validator`
- parent-relative imports such as `from ..utils import url_validator`
- submodule imports such as `from app.api import documentation`

This improves the accuracy of cycle and coupling reporting in repos with nested package layouts.

---

## 2. Why the Current Design Fits the Exercise

The shipped implementation is intentionally heuristic because the exercise values:
- clear output
- meaningful insights
- thoughtful design decisions
- smart use of tools

This feature adds visible value without requiring a full static-analysis platform. It demonstrates problem solving, architecture separation, and bonus insight generation while keeping implementation time aligned with the exercise scope.

---

## 3. Known Limitations

The current scanner is useful but intentionally bounded.

### Accuracy limitations
- Regex-based findings can produce false positives
- The scanner does not build full ASTs or language-specific semantic graphs
- It samples a limited number of source files rather than scanning the entire repository exhaustively

### Product limitations
- No finding suppression or ignore configuration yet
- No trend history or diff-versus-baseline view
- No analyzer versioning in the response payload
- No severity caps based on confirmed exploitability or taint analysis

### Operational limitations
- Runs inline with report generation
- Results are cached in memory only
- No background processing or retry orchestration

---

## 4. Recommended Next Steps

### 4.1 Exercise-focused improvements

These improvements most directly strengthen the submission and interview discussion.

- Improve the explanation text in the UI so users understand findings are heuristic
- Add one richer demo repository fixture or documented example showing code-health output
- Add more regression tests around Python and JS import-graph extraction
- Surface a short “why this matters” summary for the overall score in the report header
- Expand dependency insight quality so code-health and project-insight sections reinforce each other better

### 4.2 Production-focused improvements

These are higher-value if the project evolves beyond the exercise.

- Add analyzer versioning and provenance to the `code_health` payload
- Move scanning to background jobs for long-running repositories
- Persist results in Redis or another shared store
- Add repository-level ignore configuration such as `.lazydoc-scan.yml`
- Introduce AST-aware analyzers or external tools for selected languages
- Add structured telemetry for analyzer latency, fallback rates, and false-positive feedback

---

## 5. Recommended Roadmap

## Phase 1: Submission polish
- Clarify heuristic scope in the UI and docs
- Add stronger import-resolution and scoring regression tests
- Improve explanation copy for score drivers and top penalties

## Phase 2: Higher-confidence analysis
- Add AST-aware Python and JS/TS checks
- Expand rules for dangerous patterns and dependency analysis
- Add ignore/suppression mechanisms

## Phase 3: Operational maturity
- Background execution
- Persistent caching
- Analyzer versioning
- Trend history and score deltas

---

## 6. Suggested Future Data Contract Additions

The current response shape is sufficient for the exercise, but a stronger production-oriented contract could add:
- `analyzer_version`
- `scanned_paths`
- `confidence_summary`
- `ignored_rules`
- `baseline_comparison`
- `generated_at`

Example future extension:

```json
{
  "code_health": {
    "grade": "B",
    "score": 83,
    "analyzer_version": "2026.04.1",
    "generated_at": "2026-04-22T10:00:00Z",
    "metrics": {
      "security_findings": 2,
      "architecture_findings": 1,
      "maintenance_findings": 3,
      "circular_dependencies": 1,
      "coupling_index": 0.37
    }
  }
}
```

---

## 7. Recommendation Summary

The current code-health feature is already a strong bonus capability for the exercise. The best immediate next step is not “make it huge,” but “make it clearer, more trustworthy, and slightly deeper.”

Recommended priority order:
1. Strengthen messaging and regression coverage
2. Improve rule precision and import-graph accuracy further
3. Add production-ready operational controls only if the project continues beyond the exercise
