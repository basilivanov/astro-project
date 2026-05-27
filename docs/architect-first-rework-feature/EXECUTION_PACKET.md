# Execution Packet: Architect-first rework feature

## Objective
Reviewer rework should default to a single architect-bounded direct coder packet

## Slice
- slice_id: `SLICE-FEAT-ARCH-FIRST-REWORK`
- slice_dir: `/opt/astro-project/docs/architect-first-rework-feature`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/architect-first-rework-feature/requirements.slice.architect-first-rework-feature.xml`
- `/opt/astro-project/docs/architect-first-rework-feature/development-plan.slice.architect-first-rework-feature.xml`
- `/opt/astro-project/docs/architect-first-rework-feature/verification-matrix.slice.architect-first-rework-feature.md`
- `/opt/astro-project/docs/architect-first-rework-feature/knowledge-graph.slice.architect-first-rework-feature.xml`

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
