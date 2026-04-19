---
name: assignment-rubric-checklist
description: "Generate a scoring rubric checklist for the GitHub repository research tool exercise, mapped to requirements, quality, UX, and delivery expectations."
argument-hint: "Provide the project summary, key files, optional weighting, and whether to score as MVP or polished submission."
---
Create a strict, reviewer-ready scoring rubric for this technical exercise.

## Inputs
- Assignment requirements and evaluation criteria.
- Current implementation summary.
- Evidence from code, docs, and UI behavior.

## Rubric Rules
- Score each criterion from 0 to 5.
- Provide weighted and unweighted totals.
- Mark each criterion as Pass, Needs Work, or Missing.
- Include concrete evidence for each score.
- Avoid vague feedback.

## Required Criteria
1. Core feature completeness
2. Report quality and insight depth
3. System design and architecture clarity
4. Code quality and readability
5. UI and report readability
6. Edge-case handling (invalid URL, not found, rate limits)
7. Performance and efficiency considerations
8. Test or verification coverage
9. Run instructions and developer onboarding quality
10. Design decisions, trade-offs, AI usage transparency, future improvements

## Output Format
Return exactly these sections:

1) Score Summary
- Table with: Criterion, Score (0-5), Weight, Weighted Score, Status.
- Final weighted score out of 100.
- Final recommendation: Strong Pass, Pass, Borderline, or Not Ready.

2) Evidence Checklist
- Checklist with requirement-by-requirement evidence links or file references.

3) Top Gaps
- Up to 5 highest-impact deficiencies.
- Why each matters for evaluator confidence.

4) 4-Hour Improvement Plan
- Prioritized, time-boxed actions to raise score quickly.
- Include expected score impact per action.

5) Risk Notes
- Any assumptions or unknowns that could change scoring.
