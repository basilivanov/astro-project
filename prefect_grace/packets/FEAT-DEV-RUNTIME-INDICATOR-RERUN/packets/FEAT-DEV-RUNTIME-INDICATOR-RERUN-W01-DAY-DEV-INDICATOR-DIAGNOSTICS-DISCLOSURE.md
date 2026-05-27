# Packet: FEAT-DEV-RUNTIME-INDICATOR-RERUN-W01-DAY-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Summary
Inspect and, only if drift exists, repair the existing compact Day/home dev-only runtime diagnostics disclosure around the current runtime badge. Use only existing frontend runtime/debug state, keep production inert, and hand off targeted UI/visual/observability evidence requirements.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/layout.tsx
- /opt/astro-project/frontend/app/page.tsx
- /opt/astro-project/frontend/components/today/day-runtime-diagnostics-disclosure.tsx
- /opt/astro-project/frontend/components/today/daybrief-sections.tsx
- /opt/astro-project/frontend/hooks/useTelegram.ts
- /opt/astro-project/frontend/lib/telegram-runtime.ts
- /opt/astro-project/frontend/test/app/home-page.test.tsx
- /opt/astro-project/frontend/e2e/day-dev-indicator.spec.ts
- /opt/astro-project/frontend/e2e/day-canon-visual-evidence.spec.ts
- /opt/astro-project/frontend/e2e/telegram-signed-auth.spec.ts

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W00-PLANNER-SLICING
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W00-ARCHITECT-FORMALIZATION
- Feature brief `FEAT-DEV-RUNTIME-INDICATOR-RERUN/feature-brief.md`
- Existing slice docs under `/opt/astro-project/docs/expandable-day-screen-dev-indicator`
- Root canon entries for `SCN-DAY-DEV-RUNTIME-INDICATOR`, `FLOW-DAY-DEV-RUNTIME-INDICATOR`, and `VM-DAY-DEV-RUNTIME-INDICATOR`

## Acceptance Criteria
- The existing DEV chip remains compact and visually local in collapsed state.
- On `/` in non-production only, tapping the chip expands and collapses a local disclosure.
- The visible disclosure body contains exactly render path, bootstrap result, and current mode from existing runtime/debug state.
- Missing diagnostics values fall back to stable `unknown` or `unavailable` values without blocking the Day screen.
- Production and non-home routes remain inert and visually unchanged.
- No backend payloads, scoring, explainability, DayBrief contracts, business logic, or Week surfaces are changed.
- Targeted unit and Playwright coverage are added or updated only if current coverage does not already prove expand, collapse, fallback, and production-inert behavior.
- If implementation already satisfies the slice, the packet may be a no-op code pass with explicit evidence handoff notes.

## Verification Profile
- backend: No backend verification lane is required because backend scope is frozen and the feature is frontend-only helper UI.
- frontend: Run targeted home-page unit coverage plus Day disclosure Playwright/visual lanes.
- observability: Run the Today post-test review after targeted frontend verification and record an explicit verdict for the touched flow.
- execution:
  - frontend: `corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx`
  - frontend: `./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts`
  - frontend: `./scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator"`
  - observability: `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md`

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff stays inside the architect allowed write scope and does not touch frozen backend, Week, or `frontend/lib/day-brief.ts` surfaces.
- No new diagnostics fields, banners, screens, backend requests, or payload dependencies are introduced.
- Interactive behavior is route-gated to `/` and production inertness is covered by code path plus test coverage.
- The reviewer can trace every acceptance criterion to a concrete code path, no-op evidence, or test assertion.
- Verification handoff identifies exact commands and expected screenshot/evidence surfaces.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-RERUN-W00-PLANNER-SLICING

## Notes
- Confirm current runtime sources before editing: `renderPath` from `FeedLayout` in `frontend/app/page.tsx`; `mode` and `bootstrapOutcome` from `useTelegram()`.
- Treat the shell-owned badge route gate as the first implementation risk; escalate instead of widening behavior if interaction leaks outside `/`.
- Touch `useTelegram.ts`, `telegram-runtime.ts`, or `telegram-signed-auth.spec.ts` only if existing audited fields or selectors require minimal alignment for this slice.
- If no dedicated production Playwright host exists, production proof may rely on deterministic unit coverage plus targeted non-production visual evidence.
