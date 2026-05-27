# Execution Packet: Light resume loop stop

## Objective
Do not allow repeated in-place light resume on the same packet

## Slice
- slice_id: `SLICE-FEAT-LIGHT-RESUME-LOOP-STOP`
- slice_dir: `/opt/astro-project/docs/light-resume-loop-stop`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/light-resume-loop-stop/requirements.slice.light-resume-loop-stop.xml`
- `/opt/astro-project/docs/light-resume-loop-stop/development-plan.slice.light-resume-loop-stop.xml`
- `/opt/astro-project/docs/light-resume-loop-stop/verification-matrix.slice.light-resume-loop-stop.md`
- `/opt/astro-project/docs/light-resume-loop-stop/knowledge-graph.slice.light-resume-loop-stop.xml`

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
