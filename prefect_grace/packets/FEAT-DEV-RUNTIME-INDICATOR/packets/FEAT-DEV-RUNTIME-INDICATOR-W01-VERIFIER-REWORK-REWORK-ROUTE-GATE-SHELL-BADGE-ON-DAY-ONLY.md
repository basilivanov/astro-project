# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-REWORK-REWORK-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY

## Summary
Validate the localized rework for `FEAT-DEV-RUNTIME-INDICATOR-W01-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W01-REWORK-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY
- FEAT-DEV-RUNTIME-INDICATOR-W01-REVIEWER-TECHNICAL-VERDICT

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the rework.

## Verification Profile
- backend: rerun minimally sufficient backend checks for the reworked scope
- frontend: rerun targeted frontend checks if UI changed
- observability: repeat post-test digest, trace, and replay review

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access
- runner: verifier
- backend_profile: backend_quick
- frontend_commands:
  - {'required_commands': ['corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx', './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts', './scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"'], 'visual_verification': {'status': 'evidence_collection', 'artifacts': ['Dev-collapsed screenshot', 'Dev-expanded screenshot', 'Production-unchanged screenshot or documented production-host limitation with unit substitution']}, 'evidence': ['Verifier records exact commands executed and their outcomes.'], 'verdict_expectation': 'pass'}
- observability_commands:
  - {'required_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'evidence': ['Verifier captures the latest digest, replay, trace, and degradation signals relevant to the Day disclosure flow.'], 'verdict_expectation': 'clean_or_explained_degraded'}
- artifact_globs:
  - frontend/test-results/**/*
  - test-results/**/*
  - artifacts/**/*
- touches_frontend: True
- requires_frontend_visual: True
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W01-REWORK-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY

## Notes
- This verifier packet was auto-created from reviewer blockers.
