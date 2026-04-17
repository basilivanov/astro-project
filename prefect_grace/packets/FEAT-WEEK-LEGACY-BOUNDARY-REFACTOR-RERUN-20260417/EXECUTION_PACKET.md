# Execution Packet: Week Legacy Boundary Refactor Rerun 20260417

## Objective
Re-run the Week legacy boundary scope as a clean feature line: preserve canonical Week continuity, fail closed when canonical Week payload is absent, and keep frontend Week compatibility reconstruction explicit and isolated.

## Slice
- slice_id: `SLICE-WEEK-LEGACY-BOUNDARY-RERUN-20260417`
- slice_slug: `week-legacy-boundary-rerun-20260417`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417`

## Source Of Truth
- `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/feature-brief.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/wave-plan.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417/architect_manifest.json`
- `/opt/astro-project/frontend/app/week/page.tsx`
- `/opt/astro-project/frontend/lib/week-brief.ts`
- `/opt/astro-project/frontend/lib/week-brief-compat.ts`
- `/opt/astro-project/frontend/test/app/week-page.test.tsx`
- `/opt/astro-project/frontend/test/lib/week-brief.test.ts`
- `/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts`
- `/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts`

## Impacted Modules
- `M-FRONTEND-WEEK`
- `M-WEEK-PAGE`
- `M-WEEK-BRIEF-ADAPTER`
- `M-WEEK-BRIEF-COMPATIBILITY`
- `M-WEEK-UI-STATE`

## Allowed Write Scope
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

## Frozen Scope
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

## Business Invariants
- Canonical `/week` maps only canonical `week_brief` or `week_brief_envelope.data` into the product surface.
- Legacy `week_map` and chunks may be reconstructed only through the explicit compatibility helper, not through the canonical `/week` route.
- Missing canonical Week state fails closed with honest empty/create UI.
- In-progress Week state stays top-layer only and does not expose the full completed Week sections.
- No raw internal tokens such as `legacy`, `fallback`, `week_map`, `weekbrief`, `compatibility`, `headline`, `markdown`, or `weekly report` are visible on the user-facing Week boundary.

## Verification
- `python3 -m pytest -q tests/test_week_brief_frontend_mapping.py`
- `corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts`
- `./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts`
- `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`

## Observability Policy
W01 owns packet-local/read-only evidence only. No Today/Week canonical closeout is required because this feature does not intentionally emit a canonical runtime flow; `degraded-but-expected` is acceptable when read-only evidence lacks fresh canonical emitter traces but targeted tests and visual artifacts are clean.

## Worker Deliverables
1. Code or test deltas for the active packet only.
2. Fresh targeted verification evidence.
3. Fresh visual proof for canonical Week surface and fail-closed empty state.
4. Reviewer-facing note with scope, risks, and packet-local observability verdict.
