# Packet: FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-VERIFIER-EVIDENCE

## Summary
Execute the architect-defined Day runtime indicator verification lanes, capture visual artifacts for dev-expanded/prod-inert states, and record the explicit Today observability verdict.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- coder packet file

## Acceptance Criteria
- Exact targeted verification commands are executed and their PASS/FAIL results are recorded.
- Evidence includes dev-collapsed and dev-expanded visual artifacts for the runtime indicator flow.
- Production-inert proof is recorded explicitly, with deterministic unit coverage as the minimum accepted proof when no dedicated production Playwright host is available.
- Today post-test review is executed after frontend checks and the verdict is recorded as `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.
- Evidence package includes a file-level diff summary grouped by frontend, backend, and tests.

## Verification Profile
- backend: Confirm the diff summary shows no backend writes; no backend command execution is expected for this slice.
- frontend: Run the targeted Day runtime indicator unit, Playwright, and visual-evidence lanes.
- observability: Run the Today post-test review command and record the latest relevant verdict plus identifiers present in the output.

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
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.
- Visual artifacts are attached and labeled clearly enough to distinguish collapsed, expanded, and prod-inert/prod-proof states.
- Observability evidence contains an explicit verdict and does not hide unexpected degradation.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Notes
- Fail the packet if required evidence is missing.
- Any optional production-host visual run is supplemental only; lack of that host is not a blocker if deterministic unit coverage already proves production inertness.
- If observability output is fragmented or absent, record `no-evidence-blocker` rather than treating the run as clean.
