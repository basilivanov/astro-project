# Execution Packet: Expandable dev indicator on Day screen

## Objective
Reuse the existing compact Day/home DEV chip as a dev-only runtime diagnostics disclosure without changing DayBrief contracts, backend traffic, or production behavior.

## Slice
- slice_id: `SLICE-FEAT-DAY-DEV-INDICATOR`
- slice_dir: `/opt/astro-project/docs/expandable-day-screen-dev-indicator`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/expandable-day-screen-dev-indicator/requirements.slice.expandable-day-screen-dev-indicator.xml`
- `/opt/astro-project/docs/expandable-day-screen-dev-indicator/development-plan.slice.expandable-day-screen-dev-indicator.xml`
- `/opt/astro-project/docs/expandable-day-screen-dev-indicator/verification-matrix.slice.expandable-day-screen-dev-indicator.md`
- `/opt/astro-project/docs/expandable-day-screen-dev-indicator/knowledge-graph.slice.expandable-day-screen-dev-indicator.xml`

## Impacted modules
- `M-FRONTEND-WEBAPP`
- `M-FRONTEND-TODAY`
- `M-USE-TELEGRAM`

## Allowed write scope
- `/opt/astro-project/frontend/app/layout.tsx`
- `/opt/astro-project/frontend/app/page.tsx`
- `/opt/astro-project/frontend/components/today/*`
- `/opt/astro-project/frontend/hooks/useTelegram.ts`
- `/opt/astro-project/frontend/lib/telegram-runtime.ts`
- `/opt/astro-project/frontend/test/app/home-page.test.tsx`
- `/opt/astro-project/frontend/e2e/day-dev-indicator.spec.ts`
- `/opt/astro-project/frontend/e2e/day-canon-visual-evidence.spec.ts`
- `/opt/astro-project/frontend/e2e/telegram-signed-auth.spec.ts`

## Frozen scope
- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/app/week/**`
- `/opt/astro-project/frontend/components/week/**`
- `/opt/astro-project/frontend/lib/day-brief.ts`

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
