# Execution Packet: Expandable dev indicator on Week screen rerun 2

## Objective
Rerun the already-canonical Week runtime indicator slice through the live GRACE pipeline after pipeline and reviewer-routing fixes, without widening product scope.

## Slice
- slice_id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- slice_dir: `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2/requirements.slice.expandable-week-runtime-indicator-rerun-2.xml`
- `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2/development-plan.slice.expandable-week-runtime-indicator-rerun-2.xml`
- `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2/verification-matrix.slice.expandable-week-runtime-indicator-rerun-2.md`
- `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2/knowledge-graph.slice.expandable-week-runtime-indicator-rerun-2.xml`

## Impacted modules
- `M-FRONTEND-WEBAPP`
- `M-FRONTEND-WEEK`
- `M-USE-TELEGRAM`

## Allowed write scope
- `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2/**`
- `/opt/astro-project/frontend/app/layout.tsx`
- `/opt/astro-project/frontend/app/week/page.tsx`
- `/opt/astro-project/frontend/components/week/week-runtime-diagnostics-disclosure.tsx`
- `/opt/astro-project/frontend/test/app/week-page.test.tsx`
- `/opt/astro-project/frontend/e2e/week-runtime-indicator.spec.ts`
- `/opt/astro-project/frontend/e2e/week-runtime-indicator-visual.spec.ts`
- `/opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**`

## Frozen scope
- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/app/page.tsx`
- `/opt/astro-project/frontend/components/today/**`
- `/opt/astro-project/frontend/hooks/useTelegram.ts`
- `/opt/astro-project/frontend/lib/telegram-runtime.ts`
- `/opt/astro-project/frontend/lib/week-brief.ts`
- `/opt/astro-project/frontend/components/week/week-hero-map.tsx`
- `/opt/astro-project/frontend/components/week/week-day-strip.tsx`
- `/opt/astro-project/frontend/components/week/week-day-drawer.tsx`
- `/opt/astro-project/frontend/components/week/week-domain-panel.tsx`
- `/opt/astro-project/frontend/components/week/week-actions-panel.tsx`
- `/opt/astro-project/frontend/components/week/week-explainability-panel.tsx`
- `/opt/astro-project/frontend/components/week/week-deep-sections.tsx`
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
