# Execution Packet: Planner rework feature

## Objective
Reviewer rework should escalate to architect/planner only when decomposition must change

## Slice
- slice_id: `SLICE-FEAT-PLANNER-REWORK`
- slice_dir: `/opt/astro-project/docs/planner-rework-feature`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/planner-rework-feature/requirements.slice.planner-rework-feature.xml`
- `/opt/astro-project/docs/planner-rework-feature/development-plan.slice.planner-rework-feature.xml`
- `/opt/astro-project/docs/planner-rework-feature/verification-matrix.slice.planner-rework-feature.md`
- `/opt/astro-project/docs/planner-rework-feature/knowledge-graph.slice.planner-rework-feature.xml`

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
