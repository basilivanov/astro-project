# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE`

## Summary
Produce fresh Week unit, behavior, visual, and observability evidence for the rerun and record a machine-consumable verdict for reviewer and architect closeout.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Acceptance Criteria
- All targeted Week verification commands pass against the coder output.
- Evidence includes dev-collapsed, dev-expanded, and prod-unchanged Week captures tied to the existing runtime badge entry point.
- Evidence explicitly states whether the Week top area remains local and non-banner-like.
- FLOW-TODAY-WEEK-WEEK observability review runs after fresh Week flow commands and returns clean or degraded-but-expected, not no-evidence-blocker or unexpected-degradation.
- Executed commands, PASS or FAIL status, and artifact locations are recorded for reviewer consumption.

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
- Reject if any required verification lane is skipped or only reported indirectly.
- Reject if visual evidence does not cover dev-collapsed, dev-expanded, and prod-unchanged states.
- Reject if the observability verdict is missing, fragmented, no-evidence-blocker, or unexpected-degradation.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Notes
- This packet owns the canonical Today or Week observability verdict for W01.
- If no dedicated production Playwright host is available, unit proof may satisfy production inertness only when the evidence note explicitly explains why prod-host visual proof was unavailable.
