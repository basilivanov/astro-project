# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-DIAGNOSTICS-DISCLOSURE

## Summary
Render the local Day diagnostics disclosure using only existing runtime/debug state: render path, bootstrap result, and current mode.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/page.tsx
- /opt/astro-project/frontend/components/today/*
- /opt/astro-project/frontend/hooks/useTelegram.ts
- /opt/astro-project/frontend/lib/telegram-runtime.ts
- /opt/astro-project/frontend/test/app/home-page.test.tsx

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W00-PLANNER-SLICING
- FEAT-DEV-RUNTIME-INDICATOR-W00-ARCHITECT-FORMALIZATION
- FEAT-DEV-RUNTIME-INDICATOR-W01-SHELL-BADGE-ROUTE-GATE
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/EXECUTION_PACKET.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/knowledge-graph.slice.expandable-day-screen-dev-indicator.xml

## Acceptance Criteria
- On `/` in non-production, tapping the compact chip expands a local disclosure.
- Tapping the chip again collapses the disclosure.
- The visible disclosure body includes only render path, bootstrap result, and current mode.
- Missing diagnostics sources render stable unknown or unavailable values instead of blocking the Day screen.
- The disclosure remains local to the chip area with minimal layout shift and does not become banner-like.
- DayBrief hero, domains, CTA, scoring, readiness semantics, backend payloads, and backend traffic remain unchanged.

## Verification Profile
- backend: not required; packet must not touch backend or DayBrief DTO adapter
- frontend: Run `corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx` and include PASS/FAIL. Tests must cover expand, collapse, approved three visible fields only, unavailable fallback values, and production-inert behavior.
- observability: not required for this packet alone unless browser verification is performed; final Today observability is required in FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Diff stays within listed write_scope and architect allowed_write_scope.
- No diagnostics fields beyond render path, bootstrap result, and current mode are visible.
- No payload, correlation, trace, explainability, scoring, or backend diagnostics appear in user-facing UI.
- No Week route or component files are changed.
- Unit tests prove both non-production toggle behavior and production inertness.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W01-SHELL-BADGE-ROUTE-GATE

## Notes
- Use existing runtime/debug state only.
- Do not add a new debug banner, separate diagnostics screen, or top-level product surface.
