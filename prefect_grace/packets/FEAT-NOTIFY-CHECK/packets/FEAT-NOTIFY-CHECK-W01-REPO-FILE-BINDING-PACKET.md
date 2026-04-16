# Packet: FEAT-NOTIFY-CHECK-W01-REPO-FILE-BINDING-PACKET

## Summary
Resolve architect placeholder paths to exact repository files and record them in feature-local packet artifacts before implementation begins.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- prefect_grace/packets/FEAT-NOTIFY-CHECK/**

## Inputs
- FEAT-NOTIFY-CHECK-W00-PLANNER-SLICING
- FEAT-NOTIFY-CHECK-W00-ARCHITECT-FORMALIZATION
- /opt/astro-project/docs/notify-check-day-default-execute/architect_manifest.json
- /opt/astro-project/docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/notify-check-day-default-execute/EXECUTION_PACKET.md

## Acceptance Criteria
- Concrete repo paths are identified for M-FE-DAY-RUNTIME-INDICATOR, M-FE-NOTIFY-CHECK-INTAKE-DEFAULTS, M-FE-NOTIFY-CHECK-DISPATCH, and e2e/<day-notify-check-spec>.spec.ts.
- A feature-local binding note records each concrete path and why it belongs to the Day slice.
- If any binding would require backend/**, prefect/**, or frontend/<non-day-slices>/** writes, the packet stops and records a reslice blocker instead of implementing behavior.
- No frontend behavior code is changed in this packet.

## Verification Profile
- backend: Not required; backend is frozen for this slice.
- frontend: Static artifact review only; no UI behavior change is allowed in this packet.
- observability: Artifact consistency check: bindings must align with architect manifest allowed_write_scope and frozen_scope.
- execution: {'backend_commands': [], 'frontend_commands': [], 'observability_commands': ['test -f /opt/astro-project/docs/notify-check-day-default-execute/architect_manifest.json', 'test -f /opt/astro-project/docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md', 'test -f /opt/astro-project/docs/notify-check-day-default-execute/EXECUTION_PACKET.md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['prefect_grace/packets/FEAT-NOTIFY-CHECK/**']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Reject if exact path bindings remain placeholders.
- Reject if the packet widens scope beyond architect_manifest.allowed_write_scope.
- Reject if the packet performs implementation changes before binding confirmation.
- Accept only if downstream coder_notify_default can use concrete file paths without inference.

## Dependencies
- FEAT-NOTIFY-CHECK-W00-PLANNER-SLICING

## Notes
- This packet exists because architect formalization explicitly marked file bindings as open.
- If repository inspection proves a shared helper would leak behavior to non-Day flows, route to architect reslicing instead of widening W01.
- Current repair scan binds the existing Day runtime indicator to `frontend/app/page.tsx`, `frontend/components/today/day-runtime-diagnostics-disclosure.tsx`, `frontend/components/today/daybrief-sections.tsx`, `frontend/test/app/home-page.test.tsx`, and `frontend/e2e/day-dev-indicator.spec.ts`.
- Current repair scan did not find concrete Day-owned frontend bindings for `M-FE-NOTIFY-CHECK-INTAKE-DEFAULTS` or `M-FE-NOTIFY-CHECK-DISPATCH`; if rerun confirms that, record `contract-mismatch-no-day-notify-surface` instead of forcing implementation.

## Execution Result
- Artifact inputs confirmed present:
  - `/opt/astro-project/docs/notify-check-day-default-execute/architect_manifest.json`
  - `/opt/astro-project/docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md`
  - `/opt/astro-project/docs/notify-check-day-default-execute/EXECUTION_PACKET.md`
- Concrete binding artifact recorded at `prefect_grace/packets/FEAT-NOTIFY-CHECK/FEAT-NOTIFY-CHECK-W01-BINDING-NOTE.md`.
- Binding verdict: `contract-mismatch-no-day-notify-surface`
- No frontend behavior files were edited in this packet.
