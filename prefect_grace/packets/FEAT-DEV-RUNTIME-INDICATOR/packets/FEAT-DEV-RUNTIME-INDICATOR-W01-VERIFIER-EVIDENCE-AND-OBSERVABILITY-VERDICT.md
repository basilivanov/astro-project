# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE-AND-OBSERVABILITY-VERDICT

## Summary
Collect the targeted unit, Playwright, visual, and post-test observability evidence for the slice and emit the formal verification verdict.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-DEV-RUNTIME-INDICATOR/packets/FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE.md

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W01-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY
- FEAT-DEV-RUNTIME-INDICATOR-W01-RENDER-DAY-LOCAL-DIAGNOSTICS-DISCLOSURE
- FEAT-DEV-RUNTIME-INDICATOR-W01-ADD-TARGETED-PLAYWRIGHT-AND-VISUAL-EVIDENCE
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/verification-matrix.slice.expandable-day-screen-dev-indicator.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/architect_manifest.json

## Acceptance Criteria
- Exact verification commands and PASS or FAIL outcomes are recorded for the unit and targeted Playwright lanes.
- Visual evidence is attached or explicitly linked for dev-collapsed, dev-expanded, and production-unchanged states.
- The post-test observability review is executed with the today-week profile and an explicit verdict of `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker` is recorded.
- The evidence summary confirms no backend changes and groups the diff summary by frontend and tests.

## Verification Profile
- backend: {'required_commands': [], 'evidence': ['Verifier confirms no backend write scope was touched.'], 'verdict_expectation': 'not_required'}
- frontend: {'required_commands': ['corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx', './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts', './scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"'], 'visual_verification': {'status': 'evidence_collection', 'artifacts': ['Dev-collapsed screenshot', 'Dev-expanded screenshot', 'Production-unchanged screenshot or documented production-host limitation with unit substitution']}, 'evidence': ['Verifier records exact commands executed and their outcomes.'], 'verdict_expectation': 'pass'}
- observability: {'required_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'evidence': ['Verifier captures the latest digest, replay, trace, and degradation signals relevant to the Day disclosure flow.'], 'verdict_expectation': 'clean_or_explained_degraded'}

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
- Any `unexpected-degradation` or `no-evidence-blocker` verdict blocks reviewer acceptance.
- Evidence must name exact commands, timestamps, and artifact locations rather than only summarizing outcomes.
- The verification note must state whether production-unchanged proof came from Playwright or the approved unit-based fallback.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W01-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY
- FEAT-DEV-RUNTIME-INDICATOR-W01-RENDER-DAY-LOCAL-DIAGNOSTICS-DISCLOSURE
- FEAT-DEV-RUNTIME-INDICATOR-W01-ADD-TARGETED-PLAYWRIGHT-AND-VISUAL-EVIDENCE

## Notes
- Post-test observability is mandatory because the slice touches Today.
- Do not treat green tests alone as sufficient evidence.
