# Packet: FEAT-DEV-RUNTIME-INDICATOR-RERUN-3-W01-VERIFIER-EVIDENCE

## Summary
Validate the coder packet with the required test profile and observability gate.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-3-W01-DAY-DEV-RUNTIME-INDICATOR-DISCLOSURE-RERUN
- coder packet file

## Acceptance Criteria
- Commands run are recorded.
- Evidence paths are recorded.
- Observability verdict is explicit.
- Frontend visual verdict is explicit when UI is touched.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- frontend_profile: frontend_quick
- frontend_commands:
  - corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx
  - ./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts
  - ./scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"
- observability_profile: today-week
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - /opt/astro-project/test-results/**/*.png
  - /opt/astro-project/frontend/test-results/**/*.png
  - /opt/astro-project/playwright-report/**/*
  - /opt/astro-project/frontend/playwright-report/**/*
  - /opt/astro-project/frontend/docs/review_evidence/**/*
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-3-W01-DAY-DEV-RUNTIME-INDICATOR-DISCLOSURE-RERUN

## Notes
- Fail the packet if evidence is missing.
