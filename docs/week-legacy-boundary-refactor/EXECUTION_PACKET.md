# Execution Packet: Week Legacy Boundary Refactor and Slice Decomposition

## Objective
Detach WeekBrief assembly from report_workflow private helpers and isolate frontend compatibility reconstruction without changing Week product semantics.

## Slice
- slice_id: `SLICE-FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- slice_dir: `/opt/astro-project/docs/week-legacy-boundary-refactor`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/week-legacy-boundary-refactor/requirements.slice.week-legacy-boundary-refactor.xml`
- `/opt/astro-project/docs/week-legacy-boundary-refactor/development-plan.slice.week-legacy-boundary-refactor.xml`
- `/opt/astro-project/docs/week-legacy-boundary-refactor/verification-matrix.slice.week-legacy-boundary-refactor.md`
- `/opt/astro-project/docs/week-legacy-boundary-refactor/knowledge-graph.slice.week-legacy-boundary-refactor.xml`

## Impacted modules
- `M-REPORT-WORKFLOW`
- `M-WEEK-BRIEF-SEED`
- `M-WEEK-BRIEF-SERVICE`
- `M-FRONTEND-WEEK`
- `M-WEEK-BRIEF-COMPATIBILITY`

## Allowed write scope
- `/opt/astro-project/backend/app/services/week_brief_seed.py`
- `/opt/astro-project/backend/app/services/week_brief_service.py`
- `/opt/astro-project/backend/app/services/report_workflow.py`
- `/opt/astro-project/frontend/lib/week-brief.ts`
- `/opt/astro-project/frontend/lib/week-brief-compat.ts`
- `/opt/astro-project/tests/test_week_brief_service.py`
- `/opt/astro-project/tests/test_week_brief_api.py`
- `/opt/astro-project/tests/test_week_brief_frontend_mapping.py`
- `/opt/astro-project/frontend/test/lib/week-brief.test.ts`
- `/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts`
- `/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts`

## Frozen scope
- `/opt/astro-project/backend/app/main.py`
- `/opt/astro-project/backend/app/services/week_map.py`
- `/opt/astro-project/backend/app/services/day_brief*`
- `/opt/astro-project/frontend/app/week/page.tsx`
- `/opt/astro-project/frontend/components/week/**`
- `/opt/astro-project/frontend/app/read/**`

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
