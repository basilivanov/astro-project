# Execution Packet: Notify check

## Objective
Determine whether FEAT-NOTIFY-CHECK can implement Day-slice-only execute=true defaulting, and stop on contract mismatch if the current repo lacks a Day-owned Notify-check intake/default/dispatch surface.

## Slice
- slice_id: `SLICE-FEAT-NOTIFY-CHECK`
- slice_dir: `/opt/astro-project/docs/notify-check-day-default-execute`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/notify-check-day-default-execute/requirements.slice.notify-check-day-default-execute.xml`
- `/opt/astro-project/docs/notify-check-day-default-execute/development-plan.slice.notify-check-day-default-execute.xml`
- `/opt/astro-project/docs/notify-check-day-default-execute/verification-matrix.slice.notify-check-day-default-execute.md`
- `/opt/astro-project/docs/notify-check-day-default-execute/knowledge-graph.slice.notify-check-day-default-execute.xml`

## Impacted modules
- `M-FE-DAY-RUNTIME-INDICATOR`
- `M-FE-NOTIFY-CHECK-INTAKE-DEFAULTS`
- `M-FE-NOTIFY-CHECK-DISPATCH`

## Allowed write scope
- `requirements.xml`
- `development-plan.xml`
- `knowledge-graph.xml`
- `verification-matrix.md`
- `docs/notify-check-day-default-execute/**`
- `prefect_grace/packets/FEAT-NOTIFY-CHECK/**`

## Frozen scope
- `backend/**`
- `prefect/**`
- `frontend/**`

## Execution policy
- Respect the slice requirements and write scope exactly.
- Do not widen scope without architect approval.
- If a crash or 500 appears, add or update a reproduction test before claiming green.
- Verification must include post-test observability review when the slice touches a required surface.

## Worker deliverables
1. Code changes for the active packet only.
2. Updated or added tests for the affected slice.
3. Verification evidence and observability verdict.
4. Short reviewer-facing note: risks, open questions, and whether the next packet is unblocked.
