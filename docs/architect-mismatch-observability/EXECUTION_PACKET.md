# Execution Packet: Architect mismatch observability

## Objective
Reject planner today-week gate when architect did not authorize canonical evidence ownership

## Slice
- slice_id: `SLICE-FEAT-ARCH-MISMATCH-OBS`
- slice_dir: `/opt/astro-project/docs/architect-mismatch-observability`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/architect-mismatch-observability/requirements.slice.architect-mismatch-observability.xml`
- `/opt/astro-project/docs/architect-mismatch-observability/development-plan.slice.architect-mismatch-observability.xml`
- `/opt/astro-project/docs/architect-mismatch-observability/verification-matrix.slice.architect-mismatch-observability.md`
- `/opt/astro-project/docs/architect-mismatch-observability/knowledge-graph.slice.architect-mismatch-observability.xml`

## Impacted modules
- `M-FRONTEND-WEEK`

## Allowed write scope
- `/opt/astro-project/frontend/app/week/page.tsx`

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
