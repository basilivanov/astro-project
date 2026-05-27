# Execution Packet: Prefect Native Queue Smoke

## Objective
Verify that batch submission lands in Prefect as Scheduled and respects queue concurrency.

## Slice
- slice_id: `SLICE-FEAT-PREFECT-NATIVE-QUEUE-SMOKE`
- slice_dir: `/opt/astro-project/docs/prefect-native-queue-smoke`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`

## Impacted modules
- `-`

## Allowed write scope
- `See packet contract and architect scope.`

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
