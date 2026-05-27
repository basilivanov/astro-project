# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE`

## Summary
Implement or tighten the bounded Week-only runtime disclosure behavior from the existing shell badge entry point and keep the targeted Week tests aligned with that behavior.

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
- /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-ARCHITECT-FORMALIZATION

## Acceptance Criteria
- Any implementation delta stays inside the approved Week runtime indicator slice and does not modify frozen backend, Today, Telegram hook, or WeekBrief surfaces.
- On /week in non-production, the existing compact chip toggles a local disclosure that shows only render path, bootstrap result, and current mode, with stable unknown or unavailable fallbacks when source values are absent.
- Collapsed state stays compact, expanded state stays local to the chip area, and production plus non-Week routes remain inert and visually unchanged.
- Week render-path labels remain stable for canonical, in_progress, empty, error, auth_gate, and loading branches.
- Targeted Week unit and Playwright coverage is updated or confirmed so the downstream verifier can capture dev-collapsed, dev-expanded, and prod-unchanged proof without widening scope.

## Verification Profile
- backend: No backend lane; backend files, payload contracts, and business logic must remain untouched.
- frontend: Run the targeted Week unit lane and the dedicated Week disclosure behavior lane; leave the visual lane verifier-ready for dev-collapsed, dev-expanded, and prod-unchanged proof.
- observability: Packet-local only; coder self-check may inspect local failures, but canonical FLOW-TODAY-WEEK-WEEK observability remains owned by the wave-final verifier.
- execution:
  - backend_commands:
  - frontend_commands:
    - corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx
    - ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Reject if visible diagnostics fields exceed render path, bootstrap result, and current mode.
- Reject if the disclosure becomes interactive outside non-production /week or turns the Week top area into a banner-like surface.
- Reject if frozen modules or backend-adjacent files are modified.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-PLANNER-SLICING

## Notes
- This is the single coder packet for W01; keep the implementation bounded to the existing shell badge and Week helper-state lane.
- A no-op product diff is acceptable only if targeted tests or selectors remain verifier-ready and the downstream verifier can still capture fresh evidence.
