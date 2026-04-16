# Execution Packet: Expandable dev indicator on Week screen

## Objective
Reuse the existing compact Week DEV chip as a dev-only runtime diagnostics disclosure without changing Week content, backend payloads, scoring, or production behavior.

## Slice
- slice_id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR`
- slice_dir: `/opt/astro-project/docs/expandable-week-runtime-indicator`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/expandable-week-runtime-indicator/requirements.slice.expandable-week-runtime-indicator.xml`
- `/opt/astro-project/docs/expandable-week-runtime-indicator/development-plan.slice.expandable-week-runtime-indicator.xml`
- `/opt/astro-project/docs/expandable-week-runtime-indicator/verification-matrix.slice.expandable-week-runtime-indicator.md`
- `/opt/astro-project/docs/expandable-week-runtime-indicator/knowledge-graph.slice.expandable-week-runtime-indicator.xml`

## Impacted modules
- `M-FRONTEND-WEBAPP`
- `M-FRONTEND-WEEK`
- `M-USE-TELEGRAM`

## Allowed write scope
- `/opt/astro-project/frontend/app/layout.tsx`
- `/opt/astro-project/frontend/app/week/page.tsx`
- `/opt/astro-project/frontend/components/week/week-runtime-diagnostics-disclosure.tsx`
- `/opt/astro-project/frontend/test/app/week-page.test.tsx`
- `/opt/astro-project/frontend/e2e/week-runtime-indicator.spec.ts`
- `/opt/astro-project/frontend/e2e/week-runtime-indicator-visual.spec.ts`
- `/opt/astro-project/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**`

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
