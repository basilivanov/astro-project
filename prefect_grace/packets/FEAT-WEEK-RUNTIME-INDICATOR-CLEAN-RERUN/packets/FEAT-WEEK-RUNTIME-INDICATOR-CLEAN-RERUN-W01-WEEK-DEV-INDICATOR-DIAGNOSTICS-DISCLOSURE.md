# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE`

## Summary
Implement or correct the existing Week-only dev indicator disclosure so the compact chip expands and collapses local runtime diagnostics in non-production while production and non-Week routes remain inert.

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
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-ARCHITECT-FORMALIZATION

## Acceptance Criteria
- The existing Week DEV chip remains compact when collapsed.
- On /week in non-production, tapping the chip expands a local diagnostics disclosure.
- Tapping the chip again collapses the local diagnostics disclosure.
- The disclosure body shows only render path, bootstrap result, and current mode.
- Render path labels are derived from existing Week page states and remain stable for canonical, in_progress, empty, error, auth_gate, and loading branches.
- Absent diagnostics values render stable unknown or unavailable text without crashing /week.
- Production mode leaves the indicator visually unchanged and inert.
- Non-Week routes do not show the Week diagnostics disclosure.
- No backend, WeekBrief, useTelegram internals, Day screen, scoring, explainability, payload, or business-logic files are changed.
- Tests are added or updated only in the approved Week unit and Playwright files.

## Verification Profile
- backend: No backend verification is expected because backend scope is frozen and must remain unchanged.
- frontend: Coder should run targeted Week unit and Playwright checks for the affected helper behavior before handoff when feasible.
- observability: Coder does not own canonical observability. Packet-local evidence is finalized by the verifier.
- execution:
  - backend_commands:
  - frontend_commands:
    - corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**
    - /opt/astro-project/frontend/test-results/**
    - /opt/astro-project/frontend/playwright-report/**

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Reject if any file outside the packet write scope is changed without architect approval.
- Reject if backend, Day, WeekBrief, useTelegram internals, or unrelated Week panel scope is touched.
- Reject if the disclosure exposes diagnostics beyond render path, bootstrap result, and current mode.
- Reject if production mode becomes interactive or visually changed.
- Reject if non-Week routes can show the Week diagnostics disclosure.
- Reject if UI behavior is implemented without corresponding unit and Playwright coverage.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-ARCHITECT-FORMALIZATION

## Notes
- This packet is the only implementation packet because the architect identified the shell event, Week page state, disclosure component, and tests as one tightly coupled helper lane.
- Do not introduce canonical Today/Week flow emission or today-week post-test review in this packet.
- If route-gating cannot be preserved without touching frozen surfaces, stop and escalate.
