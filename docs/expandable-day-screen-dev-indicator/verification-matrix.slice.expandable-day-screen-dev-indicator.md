# Expandable dev indicator on Day screen Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-DAY-DEV-INDICATOR`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-DAY-DEV-INDICATOR-UNIT` | `SCN-SLICE-DEV-EXPAND, SCN-SLICE-DEV-COLLAPSE, SCN-SLICE-PROD-INERT` | corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx | Unit coverage proves the chip toggles only in non-production on `/`, falls back safely when state is absent, and keeps the production branch inert. |
| `VM-DAY-DEV-INDICATOR-E2E` | `SCN-SLICE-DEV-EXPAND, SCN-SLICE-DEV-COLLAPSE, SCN-SLICE-PROD-INERT` | ./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts; ./scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator" | Playwright proves expand/collapse behavior in the active dev stack and records collapsed, expanded, and production-unchanged visual evidence. |
| `VM-DAY-DEV-INDICATOR-OBS` | `Day disclosure slice closeout` | python3 tools/post_test_review.py --profile today-week --since 30m --report-format md | An explicit Today observability verdict is recorded after targeted verification and shows `clean` or an explained non-blocking degraded state. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/expandable-day-screen-dev-indicator`
