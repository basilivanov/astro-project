# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-REWORK-REWORK-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-REWORK-REWORK-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE`

## Summary
Validate the localized rework for `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REWORK-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the rework.

## Verification Profile
- backend: No backend verification lane beyond confirming no backend commands or backend file changes are involved.
- frontend: Execute the targeted Week unit lane plus the dedicated Week disclosure behavior and visual Playwright lanes; capture dev-collapsed, dev-expanded, and prod-unchanged artifacts from the Week runtime badge flow.
- observability: Wave-final observability closeout for FLOW-TODAY-WEEK-WEEK using fresh Week runtime evidence emitted by the targeted Playwright flow commands.
- execution:
  - backend_commands:
  - frontend_commands:
    - corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
  - observability_scope: wave_final
  - canonical_flow_commands:
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
  - observability_commands:
    - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- frontend_commands:
  - corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx
  - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
  - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- canonical_flow_commands:
  - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
  - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
- observability_scope: wave_final
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**/*
- backend_profile: backend_quick
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REWORK-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Notes
- This verifier packet was auto-created from reviewer blockers.
