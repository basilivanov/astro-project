# Wave Plan: FEAT-DEV-RUNTIME-INDICATOR-RERUN

## Objective
Rerun the existing Day-screen dev-only runtime diagnostics disclosure through the live verifier/reviewer/architect pipeline, with Prefect artifacts and visual/observability evidence published for the bounded Day slice.

## Slice Boundary
- Existing slice: `SLICE-FEAT-DAY-DEV-INDICATOR`
- Existing slice docs: `/opt/astro-project/docs/expandable-day-screen-dev-indicator`
- Product boundary: Day/home route `/` only.
- Implementation boundary: frontend-only helper UI around the current compact runtime badge and existing runtime/debug state.
- Frozen scope: backend, Week surfaces, canonical DayBrief DTO adapter, scoring, explainability, payload contracts.

## Waves
1. W01 — Rerun implementation/evidence wave: inspect current implementation, repair only bounded drift if present, verify dev expand/collapse and prod-inert behavior, collect visual proof, record Today observability verdict, then reviewer/architect accept or route to rework.

## Packet Registry
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` — role `coder` — Day dev indicator diagnostics disclosure
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-VERIFIER-EVIDENCE` — role `verifier` — Verifier Evidence
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-REVIEWER-VERDICT` — role `reviewer` — Reviewer Verdict
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-ARCHITECT-WAVE-GATE` — role `architect` — Architect Wave Gate

## Dependency Rules
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` depends on FEAT-DEV-RUNTIME-INDICATOR-RERUN-W00-PLANNER-SLICING
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-VERIFIER-EVIDENCE` depends on FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-REVIEWER-VERDICT` depends on FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE, FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-VERIFIER-EVIDENCE
- `FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-ARCHITECT-WAVE-GATE` depends on FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-REVIEWER-VERDICT

## Exit Conditions
- Coder packet is completed within the Day dev-indicator write scope, with no backend, Week, DayBrief DTO, scoring, or payload-contract changes.
- Verifier records exact command outcomes, dev-collapsed/dev-expanded visual evidence, prod-inert proof, and a Today post-test observability verdict.
- Reviewer accepts or routes to rework with concrete scope/evidence blockers.
- Architect wave gate accepts only when business fit, UX/visual proof, verification evidence, and GRACE slice consistency are all satisfied.
