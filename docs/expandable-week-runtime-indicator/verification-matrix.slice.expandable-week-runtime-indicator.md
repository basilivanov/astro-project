# Expandable dev indicator on Week screen Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-WEEK-RUNTIME-INDICATOR-UNIT` | `SCN-SLICE-WEEK-DEV-EXPAND, SCN-SLICE-WEEK-DEV-COLLAPSE, SCN-SLICE-WEEK-PROD-INERT` | corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx | Unit coverage proves route gating, stable Week render-path labels, expand/collapse behavior, fallback values, and production inertness. |
| `VM-WEEK-RUNTIME-INDICATOR-E2E` | `SCN-SLICE-WEEK-DEV-EXPAND, SCN-SLICE-WEEK-DEV-COLLAPSE, SCN-SLICE-WEEK-PROD-INERT` | ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts | Playwright proves the Week disclosure expands and collapses from the existing chip in the active dev stack and remains absent when the chip is inert. |
| `VM-WEEK-RUNTIME-INDICATOR-VISUAL` | `SCN-SLICE-WEEK-DEV-EXPAND, SCN-SLICE-WEEK-PROD-INERT` | ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts | Visual evidence captures the compact collapsed chip, expanded local disclosure, and production-unchanged Week state without turning the top area into a banner. |
| `VM-WEEK-RUNTIME-INDICATOR-OBS` | `SCN-SLICE-WEEK-OBS-CLOSEOUT` | python3 tools/post_test_review.py --profile read-only --since 30m --report-format md | Packet-local evidence includes the local observability artifact identifiers and a read-only verdict classified as clean or degraded-but-expected; no-evidence-blocker remains blocking. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/expandable-week-runtime-indicator`
