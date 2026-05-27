# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-REWORK-BACKEND-WEEK-SEED-BOUNDARY

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-REWORK-BACKEND-WEEK-SEED-BOUNDARY`

## Summary
Validate the localized rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-WAVE-VERDICT

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the rework.

## Verification Profile
- backend: Run backend quick and targeted WeekBrief service/API tests exactly as authorized by the architect verification lane.
- frontend: Run targeted frontend mapping/helper tests and Week Playwright E2E guardrails through ./scripts/run_e2e.sh. Visual evidence is explicit via Playwright/rendered artifacts; visible UI files must remain untouched.
- observability: Run packet-local read-only post-test review only. Do not run today-week and do not require fresh canonical Today/Week runtime evidence because architect W01 observability_scope is packet_local.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py
  - frontend_commands:
    - python3 -m pytest -q tests/test_week_brief_frontend_mapping.py
    - corepack pnpm --dir frontend exec jest --runInBand test/lib/week-brief.test.ts
    - ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
    - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - test-results/rendered-gate/**/*
    - frontend/test-results/**/*
    - frontend/playwright-report/**/*
    - test-results/screens/**/*
    - frontend/test-results/screens/**/*
    - test-results/**/*
    - .task-logs/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py
- frontend_commands:
  - python3 -m pytest -q tests/test_week_brief_frontend_mapping.py
  - corepack pnpm --dir frontend exec jest --runInBand test/lib/week-brief.test.ts
  - ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - test-results/rendered-gate/**/*
  - frontend/test-results/**/*
  - frontend/playwright-report/**/*
  - test-results/screens/**/*
  - frontend/test-results/screens/**/*
  - test-results/**/*
  - .task-logs/**/*
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-BACKEND-WEEK-SEED-BOUNDARY

## Notes
- This verifier packet was auto-created from reviewer blockers.
