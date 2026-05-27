# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-PACKET-LOCAL-WEEK-BOUNDARY-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-PACKET-LOCAL-WEEK-BOUNDARY-EVIDENCE`

## Summary
Run the architect-authorized verification lane for the full W01 slice and record an explicit packet-local WeekBrief observability verdict without claiming canonical Today/Week wave-final evidence.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
-

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-WEEK-E2E-GUARDRAILS
- /opt/astro-project/docs/week-legacy-boundary-refactor/verification-matrix.slice.week-legacy-boundary-refactor.md

## Acceptance Criteria
- backend quick pipeline passes.
- Targeted backend WeekBrief service/API tests pass.
- Targeted frontend mapping Python test passes.
- Targeted frontend Jest helper test passes.
- Targeted Week Playwright E2E guardrails pass through the Playwright container.
- Post-test packet-local read-only review records an explicit WeekBrief verdict of clean or degraded-but-expected.
- no-evidence-blocker and unexpected-degradation are treated as blocking verifier outcomes.
- Verifier includes exact commands, PASS/FAIL results, relevant artifact globs, and a file-level diff summary grouped by backend, frontend, and tests.

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
- Verifier evidence contains every architect-authorized command with PASS/FAIL outcome.
- Verifier explicitly classifies packet-local observability as clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker.
- Verifier does not run or require python3 tools/post_test_review.py --profile today-week for this packet-local wave.
- Verifier lists frontend visual/rendered artifacts when produced by the E2E lane and states whether visible UI was untouched.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-WEEK-E2E-GUARDRAILS

## Notes
- Architect W01 observability_scope is packet_local and canonical_flow_commands are empty, so a today-week wave-final gate must not be invented.
- A degraded-but-expected observability verdict is acceptable only with explicit rationale tied to packet-local WeekBrief evidence.
