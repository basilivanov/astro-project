# Expandable dev indicator on Week screen clean rerun Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-UNIT` | `SCN-SLICE-WEEK-CLEAN-RERUN-DEV-EXPAND, SCN-SLICE-WEEK-CLEAN-RERUN-DEV-COLLAPSE, SCN-SLICE-WEEK-CLEAN-RERUN-PROD-INERT` | corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx | Unit coverage proves route gating, stable Week render-path labels, expand/collapse behavior, fallback values, and production inertness. |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-E2E` | `SCN-SLICE-WEEK-CLEAN-RERUN-DEV-EXPAND, SCN-SLICE-WEEK-CLEAN-RERUN-DEV-COLLAPSE, SCN-SLICE-WEEK-CLEAN-RERUN-PROD-INERT` | ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts | Playwright proves the Week disclosure expands and collapses from the existing chip in the active dev stack and remains absent when the chip is inert. |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-VISUAL` | `SCN-SLICE-WEEK-CLEAN-RERUN-VISUAL-PROOF` | ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts | Visual evidence captures the compact collapsed chip, expanded local disclosure, and production-unchanged Week state without turning the top area into a banner. |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-OBS` | `SCN-SLICE-WEEK-CLEAN-RERUN-PACKET-LOCAL-EVIDENCE` | python3 tools/post_test_review.py --profile read-only --since 30m --report-format md | Packet-local evidence includes the visual spec's week-runtime-indicator-observability.json identifiers under frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator plus a read-only verdict classified as clean or degraded-but-expected. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean-rerun`
