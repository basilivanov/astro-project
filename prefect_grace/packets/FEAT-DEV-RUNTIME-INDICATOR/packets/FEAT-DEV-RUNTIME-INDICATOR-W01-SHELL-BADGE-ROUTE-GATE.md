# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-SHELL-BADGE-ROUTE-GATE

## Summary
Make the existing compact DEV/PROD chip safely reusable as a Day-route-only interaction entry point without changing non-Day surfaces or production behavior.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/layout.tsx
- /opt/astro-project/frontend/test/app/home-page.test.tsx

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING
- FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/architect_manifest.json
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/requirements.slice.expandable-day-screen-dev-indicator.xml
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/development-plan.slice.expandable-day-screen-dev-indicator.xml

## Acceptance Criteria
- The existing chip remains visually compact in collapsed state.
- The chip exposes a deterministic selector suitable for dedicated Day verification.
- New interactive behavior is route-gated to `/` only.
- Production mode remains inert and does not render or expose diagnostics disclosure behavior.
- No backend, Week, or DayBrief adapter files are touched.

## Verification Profile
- backend: not required; no backend files or payload contracts may change
- frontend: Run `corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx` and include PASS/FAIL. Unit coverage must prove route-gated non-production behavior and production-inert behavior for the shell-owned chip.
- observability: not required for this packet alone unless the route renders in browser verification; final Today observability is required in FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to /opt/astro-project/frontend/app/layout.tsx and /opt/astro-project/frontend/test/app/home-page.test.tsx.
- Route gating cannot leak new disclosure behavior to non-`/` routes.
- Production branch is inert by deterministic test, not by visual assertion alone.
- No new top-level banner, diagnostics screen, backend request, payload field, or DayBrief contract change is introduced.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING

## Notes
- This packet handles the main known risk from the architect artifacts: the chip is shell-owned and fixed-position.
- If the shell badge cannot be reused on `/` without leaking behavior into non-Day routes, stop and escalate to architect rather than widening scope.
