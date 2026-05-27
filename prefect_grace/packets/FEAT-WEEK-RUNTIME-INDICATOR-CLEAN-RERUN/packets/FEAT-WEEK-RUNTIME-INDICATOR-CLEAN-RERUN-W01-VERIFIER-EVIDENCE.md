# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-VERIFIER-EVIDENCE`

## Summary
Execute the architect-authorized targeted frontend verification and packet-local read-only observability review, then record evidence for Week dev-collapsed, dev-expanded, and prod-unchanged states.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Acceptance Criteria
- Week unit verification passes for route gating, render-path labels, fallback values, expand and collapse behavior, and production inertness.
- Week Playwright behavior verification passes for expansion, collapse, and inert production behavior.
- Week visual verification captures dev-collapsed, dev-expanded, and prod-unchanged states.
- Visual evidence shows the Week top area remains local, compact, and not banner-like.
- Packet-local read-only observability verdict is explicitly classified as clean or degraded-but-expected.
- Packet-local evidence includes week-runtime-indicator-observability identifiers when produced by the visual lane.
- Verifier does not claim canonical Today/Week closeout ownership.

## Verification Profile
- backend: No backend commands are expected; verifier should confirm backend scope remains untouched by reviewing changed files.
- frontend: Run targeted Week unit, behavior, and visual verification. Visual evidence must include dev-collapsed, dev-expanded, and prod-unchanged Week states.
- observability: Run packet-local read-only review only. Accepted verdicts are clean or degraded-but-expected when Week-local identifiers remain attributable and no unexpected Week degradation appears.
- execution:
  - backend_commands:
  - frontend_commands:
    - corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
    - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**
    - /opt/astro-project/frontend/test-results/**
    - /opt/astro-project/frontend/playwright-report/**

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- frontend_commands:
  - corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx
  - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
  - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**
  - /opt/astro-project/frontend/test-results/**
  - /opt/astro-project/frontend/playwright-report/**
- backend_profile: backend_quick
- include_day_live_canary: False

## Reviewer Gate
- Reject if any required frontend command is not executed or lacks a pass/fail result.
- Reject if visual evidence does not include dev-collapsed, dev-expanded, and prod-unchanged Week states.
- Reject if the observability verdict is unexpected-degradation or no-evidence-blocker.
- Reject if the verifier uses canonical Today/Week emission or today-week review for this packet-local wave.
- Reject if evidence artifacts are stored outside the architect-approved evidence path without explanation.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Notes
- The read-only observability review is packet-local and must not be treated as canonical business-flow evidence.
- A degraded-but-expected verdict is acceptable only when evidence is attributable and no unexpected Week degradation appears.
