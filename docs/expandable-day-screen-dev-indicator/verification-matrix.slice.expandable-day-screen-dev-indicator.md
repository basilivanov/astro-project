# Expandable dev indicator on Day screen Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-DAY-DEV-INDICATOR`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-DAY-DEV-INDICATOR-UNIT` | `SCN-SLICE-DEV-EXPAND, SCN-SLICE-DEV-COLLAPSE, SCN-SLICE-PROD-INERT` | corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx | Unit coverage proves route gating, expand collapse behavior, safe fallback values, and production inertness. |
| `VM-DAY-DEV-INDICATOR-E2E` | `SCN-SLICE-DEV-EXPAND, SCN-SLICE-DEV-COLLAPSE, SCN-SLICE-PROD-INERT` | ./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts; ./scripts/run_e2e.sh e2e/day-canon-visual-evidence.spec.ts -g "runtime indicator" | Playwright proves expand and collapse behavior in the active dev stack and captures dev-collapsed, dev-expanded, and prod-inert visual evidence. |
| `VM-DAY-DEV-INDICATOR-OBS` | `SCN-SLICE-RERUN-EVIDENCE` | python3 tools/post_test_review.py --profile read-only --since 30m --report-format md | Packet-local post-test evidence is explicit, attributable to the Day helper rerun, and classified as clean or degraded-but-expected. |
| `VM-DAY-DEV-INDICATOR-ARTIFACTS` | `SCN-SLICE-RERUN-EVIDENCE` | Review published Prefect artifacts for W01 coder verifier reviewer architect packet runs | All live rerun packet artifacts are published and inspectable. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/expandable-day-screen-dev-indicator`
