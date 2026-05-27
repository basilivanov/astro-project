# Expandable dev indicator on Week screen rerun 2 Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-WEEK-RUNTIME-INDICATOR-RERUN-2-UNIT` | `SCN-SLICE-WEEK-RERUN-2-DEV-EXPAND` | corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx | Unit coverage proves route gating, stable Week render-path labels, expand/collapse behavior, fallback values, and production inertness. |
| `VM-WEEK-RUNTIME-INDICATOR-RERUN-2-E2E` | `SCN-SLICE-WEEK-RERUN-2-DEV-COLLAPSE` | ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts | Playwright proves the Week disclosure expands and collapses from the existing chip in the active dev stack and remains absent when the chip is inert. |
| `VM-WEEK-RUNTIME-INDICATOR-RERUN-2-VISUAL` | `SCN-SLICE-WEEK-RERUN-2-VISUAL-PROOF` | ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts | Visual evidence captures the compact collapsed chip, expanded local disclosure, and production-unchanged Week state without turning the top area into a banner. |
| `VM-WEEK-RUNTIME-INDICATOR-RERUN-2-OBS` | `SCN-SLICE-WEEK-RERUN-2-OBS-CLOSEOUT` | python3 tools/post_test_review.py --profile today-week --since 30m --report-format md | Post-test review records an explicit Week verdict for FLOW-TODAY-WEEK-WEEK, and the verdict is clean or degraded-but-expected. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2`
