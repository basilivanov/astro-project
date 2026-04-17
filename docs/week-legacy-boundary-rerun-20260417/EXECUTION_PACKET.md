# Execution Packet: Week legacy boundary refactor rerun

## Objective
Preserve canonical Week continuity, fail-closed empty-state behavior, and explicit frontend Week compatibility isolation without product regression.

## Slice
- slice_id: `SLICE-WEEK-LEGACY-BOUNDARY-RERUN-20260417`
- slice_dir: `/opt/astro-project/docs/week-legacy-boundary-rerun-20260417`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`

## Impacted modules
- `M-FRONTEND-WEEK`
- `M-WEEK-PAGE`
- `M-WEEK-BRIEF-ADAPTER`
- `M-WEEK-BRIEF-COMPATIBILITY`
- `M-WEEK-UI-STATE`

## Allowed write scope
- `/opt/astro-project/frontend/app/week/**`
- `/opt/astro-project/frontend/components/week/**`
- `/opt/astro-project/frontend/lib/week-brief.ts`
- `/opt/astro-project/frontend/lib/week-brief-compat.ts`
- `/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts`
- `/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts`
- `/opt/astro-project/frontend/test/app/week-page.test.tsx`
- `/opt/astro-project/frontend/test/lib/week-brief.test.ts`
- `/opt/astro-project/tests/test_week_brief_frontend_mapping.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/**`
- `/opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417/**`

## Frozen scope
- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/app/create/**`
- `/opt/astro-project/frontend/app/page.tsx`
- `/opt/astro-project/frontend/app/read/**`
- `/opt/astro-project/frontend/hooks/useTelegram.ts`
- `/opt/astro-project/billing/**`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`

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
