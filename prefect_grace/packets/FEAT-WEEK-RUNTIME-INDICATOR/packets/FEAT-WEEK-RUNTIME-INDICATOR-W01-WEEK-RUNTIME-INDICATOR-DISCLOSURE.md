# Packet: FEAT-WEEK-RUNTIME-INDICATOR-W01-WEEK-RUNTIME-INDICATOR-DISCLOSURE

## Summary
Implement the bounded Week runtime indicator slice by reusing the existing compact shell chip on /week as a dev-only disclosure entry point, deriving render-path labels from existing Week states, and adding targeted unit and Playwright coverage.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/layout.tsx
- /opt/astro-project/frontend/app/week/page.tsx
- /opt/astro-project/frontend/components/week/week-runtime-diagnostics-disclosure.tsx
- /opt/astro-project/frontend/test/app/week-page.test.tsx
- /opt/astro-project/frontend/e2e/week-runtime-indicator.spec.ts
- /opt/astro-project/frontend/e2e/week-runtime-indicator-visual.spec.ts

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION

## Acceptance Criteria
- The existing shell DEV/PROD chip is route-eligible on /week without changing production behavior or unrelated routes.
- In non-production on /week, tapping the compact chip expands and collapses a local diagnostics disclosure.
- The visible disclosure body contains only render path, bootstrap result, and current mode.
- Render-path labels are derived from existing Week page states and remain stable for loading, auth_gate, empty, in_progress, error, and canonical branches.
- Absent diagnostics values render stable unknown or unavailable values and never crash /week or leak raw objects.
- No backend files, backend payloads, scoring, explainability contracts, WeekBrief contracts, Day surfaces, or frozen Week product components are changed.
- Targeted Week unit, behavior E2E, visual E2E, and observability commands are runnable and documented by the packet result.

## Verification Profile
- backend: No backend execution is required because this slice must not touch backend code, backend payloads, scoring, or business logic. The coder must report that backend diff scope is empty.
- frontend: Run the targeted Week unit and Playwright lanes for route gating, render-path labels, expand/collapse behavior, production inertness, and visual containment of the Week top area.
- observability: Run the Week post-test review for FLOW-TODAY-WEEK-WEEK after frontend checks and record an explicit verdict of clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker.
- execution: {'backend_commands': [], 'frontend_commands': ['corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx', './scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts', './scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts'], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'touches_frontend': True, 'requires_frontend_visual': True, 'visual_evidence_requirements': ['Capture the Week dev-collapsed top area showing the chip remains compact.', 'Capture the Week dev-expanded state showing a small local disclosure near the chip.', 'Capture the Week production-unchanged state showing no visible diagnostics block and no banner-like top-area change.'], 'artifact_globs': ['/opt/astro-project/frontend/test-results/**/*', '/opt/astro-project/frontend/playwright-report/**/*', '/opt/astro-project/test-results/**/*', '/opt/astro-project/playwright-report/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- All implementation and tests remain within the allowed write scope listed in the architect manifest.
- The diff does not touch any frozen backend, Day, Telegram runtime contract, WeekBrief, or frozen Week product component path.
- The disclosure is reachable only through the existing compact chip on /week in non-production.
- The disclosure visibly exposes exactly render path, bootstrap result, and current mode, with no extra diagnostics fields.
- Production inertness and non-Week inertness are covered by deterministic tests.
- Visual evidence demonstrates the expanded state is local and not banner-like.
- The observability verdict is explicit and is not unexpected-degradation or no-evidence-blocker.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION

## Notes
- Treat shell badge route gating as the first rework-prone risk; stop and escalate if /week eligibility cannot be added without altering / or unrelated routes.
- Do not add backend requests, payload fields, trace identifiers, correlation diagnostics, or user-facing payload/debug dumps.
- If a crash or 500 is found during implementation, add or update the smallest reproduction test inside the allowed frontend test scope before claiming green.
