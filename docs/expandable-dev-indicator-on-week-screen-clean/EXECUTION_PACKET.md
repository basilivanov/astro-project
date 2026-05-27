# Execution Packet: Expandable dev indicator on Week screen clean

## Objective
Implement the existing compact Week dev indicator as a local dev-only runtime diagnostics disclosure without widening scope and without forcing invalid canonical observability ownership.

## Slice
- slice_id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`
- slice_dir: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/requirements.slice.expandable-dev-indicator-on-week-screen-clean.xml`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/development-plan.slice.expandable-dev-indicator-on-week-screen-clean.xml`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/verification-matrix.slice.expandable-dev-indicator-on-week-screen-clean.md`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/knowledge-graph.slice.expandable-dev-indicator-on-week-screen-clean.xml`

## Impacted modules
- `-`

## Allowed write scope
- `See development plan slice.`

## Frozen scope
- `-`

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
