# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Summary
Re-run the dev-only Day/home disclosure on the existing compact chip, repairing only bounded drift if present, using only the audited runtime/debug fields and without changing backend traffic, payloads, or production behavior.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/layout.tsx
- /opt/astro-project/frontend/app/page.tsx
- /opt/astro-project/frontend/components/today/*
- /opt/astro-project/frontend/hooks/useTelegram.ts
- /opt/astro-project/frontend/lib/telegram-runtime.ts
- /opt/astro-project/frontend/test/app/home-page.test.tsx
- /opt/astro-project/frontend/e2e/day-dev-indicator.spec.ts
- /opt/astro-project/frontend/e2e/day-canon-visual-evidence.spec.ts
- /opt/astro-project/frontend/e2e/telegram-signed-auth.spec.ts

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION
- /opt/astro-project/prefect_grace/packets/FEAT-DEV-RUNTIME-INDICATOR/wave-plan.md
- /opt/astro-project/prefect_grace/packets/FEAT-DEV-RUNTIME-INDICATOR/feature-brief.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/architect_manifest.json
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/EXECUTION_PACKET.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/verification-matrix.slice.expandable-day-screen-dev-indicator.md

## Acceptance Criteria
- The existing DEV chip remains compact and visually local in collapsed state.
- On `/` in non-production only, tapping the chip expands and collapses a local disclosure.
- The visible disclosure body contains only render path, bootstrap result, and current mode from existing runtime/debug state.
- Missing diagnostics values fall back to stable unknown or unavailable values without blocking the Day screen.
- Production and non-home routes remain inert and visually unchanged.
- No backend payloads, scoring, explainability, DayBrief contracts, or Week surfaces are changed.
- Targeted unit and Playwright coverage are added or updated for expand, collapse, fallback, and production-inert behavior.

## Verification Profile
- backend: No backend verification lane is required because backend scope is frozen and the feature is frontend-only helper UI.
- frontend: Run targeted home-page unit coverage plus the Day disclosure and runtime-indicator Playwright lanes; visual proof must show the compact collapsed state and the expanded local disclosure.
- observability: Run packet-local read-only post-test review after targeted frontend verification and record an explicit verdict; `degraded-but-expected` is acceptable when no canonical Today/Week emitter is owned here and no unexpected Day degradation appears.
- execution: {'backend_commands': [], 'frontend_commands': ['corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx', './scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts', './scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"'], 'observability_commands': ['python3 tools/post_test_review.py --profile read-only --since 30m --report-format md'], 'observability_scope': 'packet_local', 'canonical_flow_commands': [], 'allow_degraded_but_expected': True, 'touches_frontend': True, 'requires_frontend_visual': True, 'artifact_globs': ['/opt/astro-project/test-results/**/*.png', '/opt/astro-project/frontend/test-results/**/*.png', '/opt/astro-project/playwright-report/**/*', '/opt/astro-project/frontend/playwright-report/**/*']}

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Diff stays inside the architect allowed write scope and does not touch frozen backend, Week, or `frontend/lib/day-brief.ts` surfaces.
- No new diagnostics fields, banners, screens, backend requests, or payload dependencies are introduced.
- Interactive behavior is route-gated to `/` and production inertness is covered by code path and test coverage.
- The reviewer can trace every acceptance criterion to a concrete code path or test assertion.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION

## Notes
- Treat the shell-owned badge route gate as the first implementation risk; escalate instead of widening behavior if interaction leaks outside `/`.
- Touch `useTelegram.ts`, `telegram-runtime.ts`, or `telegram-signed-auth.spec.ts` only if existing audited fields or selectors require minimal alignment for this slice.
- If no dedicated production Playwright host exists, production proof may rely on deterministic unit coverage plus the targeted non-production visual evidence lane.
- This packet is the W01 coder packet for the rerun; older split W01 route/disclosure/visual packets are historical context only unless explicitly reactivated.
