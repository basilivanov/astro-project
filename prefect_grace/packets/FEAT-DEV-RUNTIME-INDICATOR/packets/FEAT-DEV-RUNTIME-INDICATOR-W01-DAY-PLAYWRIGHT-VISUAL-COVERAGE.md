# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-PLAYWRIGHT-VISUAL-COVERAGE

## Summary
Add targeted Playwright coverage and visual evidence hooks for dev-collapsed, dev-expanded, collapse, and prod-unchanged states.

## Wave
W01

## Role
coder

## Reasoning
medium

## Write Scope
- /opt/astro-project/frontend/e2e/day-dev-indicator.spec.ts
- /opt/astro-project/frontend/e2e/day-canon-visual-evidence.spec.ts
- /opt/astro-project/frontend/e2e/telegram-signed-auth.spec.ts

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING
- FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION
- FEAT-DEV-RUNTIME-INDICATOR-W01-SHELL-BADGE-ROUTE-GATE
- FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-DIAGNOSTICS-DISCLOSURE
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/verification-matrix.slice.expandable-day-screen-dev-indicator.md

## Acceptance Criteria
- Dedicated Playwright coverage proves the Day route expands and collapses the diagnostics disclosure in the active dev stack.
- Playwright coverage proves production mode remains visually unchanged and inert.
- Visual evidence captures dev-collapsed and dev-expanded states.
- Visual evidence demonstrates the hero/top-area remains clean, compact, and non-banner-like.
- The tests use the dedicated Day dev-chip selector and do not overload unrelated Today tests.

## Verification Profile
- backend: not required; no backend files or services are modified
- frontend: Run `./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts` through the Playwright container and include PASS/FAIL. If visual evidence is implemented in day-canon-visual-evidence.spec.ts or telegram-signed-auth.spec.ts, run the touched targeted spec as well.
- observability: After targeted browser verification, FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE must run `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md` and record verdict

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Frontend visual verification is explicit and includes dev-collapsed plus dev-expanded screenshots.
- Production-unchanged proof is explicit and does not depend only on manual inspection.
- Dedicated spec coverage maps to VM-DAY-DEV-INDICATOR-E2E.
- No e2e changes introduce dependency on backend payload fields or Week surfaces.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-DIAGNOSTICS-DISCLOSURE

## Notes
- Use only Playwright-container execution via `./scripts/run_e2e.sh`.
- If page crash, hydration failure, or 500 appears, add or update the smallest reproduction test before claiming green.
