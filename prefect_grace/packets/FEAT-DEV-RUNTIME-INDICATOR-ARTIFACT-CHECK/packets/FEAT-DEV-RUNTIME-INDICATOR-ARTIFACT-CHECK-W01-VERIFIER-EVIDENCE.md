# Packet: FEAT-DEV-RUNTIME-INDICATOR-ARTIFACT-CHECK-W01-VERIFIER-EVIDENCE

## Summary
Record the expected evidence set for artifact publication.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes only.

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-ARTIFACT-CHECK-W01-DAY-DEV-RUNTIME-INDICATOR-ARTIFACT-CHECK

## Acceptance Criteria
- Verifier evidence is recorded.

## Verification Profile
- backend: not required
- frontend: consume targeted Day runtime indicator evidence
- observability: frontend-only expected degradation is acceptable
- execution: {'artifact_globs': ['/opt/astro-project/frontend/docs/review_evidence/**/*', '/opt/astro-project/test-results/**/*.png', '/opt/astro-project/frontend/test-results/**/*.png'], 'touches_frontend': True, 'frontend_commands': ['corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx', './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts', './scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"'], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'requires_frontend_visual': True}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- frontend_commands:
  - corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx
  - ./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts
  - ./scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - /opt/astro-project/frontend/docs/review_evidence/**/*
  - /opt/astro-project/test-results/**/*.png
  - /opt/astro-project/frontend/test-results/**/*.png
- include_day_live_canary: False

## Reviewer Gate
- Evidence must be present.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-ARTIFACT-CHECK-W01-DAY-DEV-RUNTIME-INDICATOR-ARTIFACT-CHECK

## Notes
- Artifact publication check verifier.
