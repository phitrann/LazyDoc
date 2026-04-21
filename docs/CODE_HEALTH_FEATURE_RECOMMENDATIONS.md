# Code Health Feature Recommendations

## 1. Goal
Add three new capabilities to LazyDoc in a phased and reliable way:
- Security Scanner
- Pattern Detection
- Health Score (A-F)

This plan focuses on fast MVP delivery first, then deeper analysis after precision and developer trust are established.

---

## 2. Recommended Rollout

## Phase 1 (MVP, fastest value)
- Security Scanner:
  - Hardcoded secrets/API keys
  - Dangerous eval-style usage
  - Debug statements in production code
- Health Score:
  - Initial weighted score and A-F grade
  - Security issue count, dead code %, circular dependencies
- UX:
  - Show findings with severity, confidence, file path, and explanation

## Phase 2 (deeper static analysis)
- Security Scanner:
  - SQL injection rules (Semgrep + language-specific sinks)
- Pattern Detection:
  - Singleton, Factory, Observer/Event, React custom hooks
  - Anti-patterns: God Objects and high coupling
- Health Score:
  - Add coupling metrics and anti-pattern impact

## Phase 3 (quality and governance)
- Differential scanning (new issues since baseline)
- Suppression/ignore support
- Trend charts (score over time)
- CI policy thresholds (warn or fail)

---

## 3. Security Scanner Design

### 3.1 Hardcoded secrets and API keys
Recommended approach:
- Regex signatures for known key formats
- Entropy-based detection for unknown tokens
- Allowlist support for safe test fixtures

Suggested tools:
- Gitleaks or detect-secrets

Output fields per finding:
- rule_id
- severity (Critical/High/Medium/Low)
- confidence (High/Medium/Low)
- file_path
- line
- redacted_snippet
- remediation

### 3.2 SQL injection
Recommended approach:
- Semgrep rules per language
- Detect user input flowing into query construction without sanitization/parameterization

Severity guidance:
- High: user input reaches SQL sink directly
- Medium: suspicious dynamic query assembly with unknown sanitization

### 3.3 Dangerous dynamic execution
Flag:
- eval
- Function constructor
- dynamic exec-like APIs

Severity guidance:
- Critical if untrusted input can reach sink
- High if usage is unsafe but input origin unknown

### 3.4 Debug statements in production code
Flag examples:
- console.log
- debugger
- print debugging
- pdb.set_trace or similar

Severity guidance:
- Low for occasional logs
- Medium if frequent in critical modules

---

## 4. Pattern Detection Design

## 4.1 Positive patterns (informational)
- Singleton:
  - Class/static instance access
  - Module-level single exported instance
- Factory:
  - Creation function returning different concrete types by condition
- Observer/Event:
  - subscribe/on + emit/publish style APIs
- React custom hooks:
  - exported functions prefixed with use and containing hook calls

## 4.2 Anti-patterns (warning)
- God Object:
  - excessive LOC
  - too many methods
  - too many external dependencies
- High coupling:
  - high import fan-in/fan-out
  - tightly connected module graph

Implementation note:
- Mark detections as heuristic with confidence score to reduce false certainty.

---

## 5. Health Score Design

## 5.1 Internal score model
Use internal 0-100 score, then map to letter grade.

Grade map:
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: below 60

## 5.2 Recommended weighted metrics
- Security issues: 40%
- Coupling and circular dependencies: 30%
- Dead code percentage: 20%
- Anti-patterns: 10%

## 5.3 Guardrails
- If any Critical security finding exists, cap max grade at C
- Normalize circular dependency impact by project/module size
- Use dead code percentage (not raw count) to avoid bias against large repos

## 5.4 Breakdown transparency
Always show:
- total score
- grade
- metric-by-metric contributions
- top penalties causing downgrade

---

## 6. Data Contract Recommendation

## 6.1 New report block
Add a new response block (example shape):

```json
{
  "code_health": {
    "grade": "B",
    "score": 83,
    "weights": {
      "security": 0.4,
      "architecture": 0.3,
      "dead_code": 0.2,
      "anti_patterns": 0.1
    },
    "metrics": {
      "security_findings": 2,
      "critical_findings": 0,
      "dead_code_percent": 6.2,
      "circular_dependencies": 1,
      "coupling_index": 0.37,
      "anti_pattern_findings": 3
    },
    "breakdown": [
      {"name": "Security", "score": 78, "impact": -9},
      {"name": "Architecture", "score": 85, "impact": -5},
      {"name": "Dead Code", "score": 92, "impact": -2},
      {"name": "Anti-patterns", "score": 80, "impact": -4}
    ]
  }
}
```

## 6.2 Findings block recommendation
Each finding should include:
- id
- category (security/pattern/anti_pattern)
- rule_name
- severity
- confidence
- file_path
- line
- message
- suggestion

---

## 7. Operational Recommendations

- Cache scan results by repository + commit SHA
- Support partial results with warnings instead of hard failures
- Add timeout budgets per analyzer
- Run analyzers independently so one failure does not cancel all insights
- Store analyzer versions to make results explainable across releases

---

## 8. False Positive Control

Must-have controls:
- Inline suppressions
- Repository-level ignore config
- Rule tuning per language
- Confidence thresholds in UI filters

Suggested config file:
- .lazydoc-scan.yml

Example controls:
- ignored_paths
- ignored_rules
- confidence_threshold
- env-specific debug allowlist

---

## 9. Suggested Initial Tech Stack

- Secret scanning: Gitleaks or detect-secrets
- Security and injection rules: Semgrep
- Dependency/cycle graph metrics:
  - JS/TS: madge or dependency-cruiser
  - Python: import graph analysis (module import DAG)
- Dead code:
  - JS/TS: ts-prune style checks
  - Python: vulture-style checks

---

## 10. Acceptance Criteria (MVP)

- Security scanner returns findings with severity and confidence
- Pattern detector identifies at least Singleton/Factory/Observer/React hooks in common cases
- Health score produces stable 0-100 and A-F output with clear breakdown
- API response includes new code_health and findings blocks
- UI shows findings list, filters, and health summary card
- Scanner works on invalid/partial repos with warning-based fallback behavior

---

## 11. Next Implementation Steps

1. Add backend schemas for code_health and findings.
2. Build Phase 1 analyzers with normalized finding model.
3. Integrate score calculator service.
4. Expose in documentation endpoint response.
5. Add frontend section and score card.
6. Add suppression configuration support.
7. Add tests for scoring and representative findings.
