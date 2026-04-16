# Week Legacy Boundary Refactor and Slice Decomposition Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-WEEK-LEGACY-BOUNDARY-BACKEND` | `SCN-SLICE-WEEK-SEED-OWNED, SCN-SLICE-WEEK-PROMPT-CONTEXT-SHARED, SCN-SLICE-WEEK-FALLBACK-STABLE` | docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py | WeekBrief assembly depends on the Week-owned seed helper, Week prompt-context wiring stays functional, and Week fallback plus telemetry semantics remain stable. |
| `VM-WEEK-LEGACY-BOUNDARY-FRONTEND-UNIT` | `SCN-SLICE-WEEK-CANONICAL-ONLY, SCN-SLICE-WEEK-COMPATIBILITY-ISOLATED` | python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/lib/week-brief.test.ts | Canonical Week mapping stays fail-closed for non-canonical inputs, and compatibility reconstruction remains explicit and isolated from the /week product path. |
| `VM-WEEK-LEGACY-BOUNDARY-E2E` | `SCN-SLICE-WEEK-CANONICAL-ONLY, SCN-SLICE-WEEK-NO-UI-DRIFT` | ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts | Week fallback safety and canonical continuity remain green with no visible Week regression. |
| `VM-WEEK-LEGACY-BOUNDARY-OBS` | `packet-local WeekBrief observability review` | python3 tools/post_test_review.py --profile read-only --since 30m --report-format md | Read-only observability review records clean or degraded-but-expected, and does not report unexpected-degradation or no-evidence-blocker. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/week-legacy-boundary-refactor`
