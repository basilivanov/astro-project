# Execution Packet: Expandable dev indicator on Week screen retry

## Objective
Retry the Week runtime indicator live pipeline with rework-loop guard and pipeline-resume safety.

## Slice
- slice_id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-RETRY`
- slice_dir: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-retry`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-retry/requirements.slice.expandable-dev-indicator-on-week-screen-retry.xml`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-retry/development-plan.slice.expandable-dev-indicator-on-week-screen-retry.xml`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-retry/verification-matrix.slice.expandable-dev-indicator-on-week-screen-retry.md`
- `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-retry/knowledge-graph.slice.expandable-dev-indicator-on-week-screen-retry.xml`

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
