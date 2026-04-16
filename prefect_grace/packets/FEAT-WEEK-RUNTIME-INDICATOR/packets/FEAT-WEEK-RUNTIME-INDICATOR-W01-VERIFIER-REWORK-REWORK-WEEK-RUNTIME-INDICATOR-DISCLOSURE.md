# Packet: FEAT-WEEK-RUNTIME-INDICATOR-W01-VERIFIER-REWORK-REWORK-WEEK-RUNTIME-INDICATOR-DISCLOSURE

## Summary
Validate the localized rework for `FEAT-WEEK-RUNTIME-INDICATOR-W01-WEEK-RUNTIME-INDICATOR-DISCLOSURE` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-W01-REWORK-WEEK-RUNTIME-INDICATOR-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the rework.

## Verification Profile
- backend: rerun minimally sufficient backend checks for the reworked scope
- frontend: rerun targeted frontend checks if UI changed
- observability: repeat post-test digest, trace, and replay review

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
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - /opt/astro-project/frontend/test-results/**/*
  - /opt/astro-project/frontend/playwright-report/**/*
  - /opt/astro-project/test-results/**/*
  - /opt/astro-project/playwright-report/**/*
- backend_profile: backend_quick
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-W01-REWORK-WEEK-RUNTIME-INDICATOR-DISCLOSURE

## Notes
- This verifier packet was auto-created from reviewer blockers.
