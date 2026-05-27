# Expandable dev indicator on Week screen clean Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-UNIT` | `SCN-SLICE-WEEK-CLEAN-DEV-EXPAND, SCN-SLICE-WEEK-CLEAN-DEV-COLLAPSE, SCN-SLICE-WEEK-CLEAN-PROD-INERT` | corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx | Unit coverage proves route gating, stable Week render-path labels, expand/collapse behavior, fallback values, and production inertness. |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-E2E` | `SCN-SLICE-WEEK-CLEAN-DEV-EXPAND, SCN-SLICE-WEEK-CLEAN-DEV-COLLAPSE, SCN-SLICE-WEEK-CLEAN-PROD-INERT` | ./scripts/run_e2e.sh e2e/week-runtime-indicator.spec.ts | Playwright proves the Week disclosure expands and collapses from the existing chip in the active dev stack and remains absent when the chip is inert. |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-VISUAL` | `SCN-SLICE-WEEK-CLEAN-DEV-EXPAND, SCN-SLICE-WEEK-CLEAN-PROD-INERT` | ./scripts/run_e2e.sh e2e/week-runtime-indicator-visual.spec.ts | Visual evidence captures the compact collapsed chip, expanded local disclosure, and production-unchanged Week state without turning the top area into a banner. |
| `VM-WEEK-RUNTIME-INDICATOR-CLEAN-OBS` | `SCN-SLICE-WEEK-CLEAN-PACKET-LOCAL-EVIDENCE` | python3 tools/post_test_review.py --profile read-only --since 30m --report-format md | Packet-local evidence includes the visual spec's `week-runtime-indicator-observability.json` identifiers plus a read-only verdict classified as `clean` or `degraded-but-expected`; `unexpected-degradation` and `no-evidence-blocker` are blocking. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence for dev-collapsed, dev-expanded, and prod-unchanged Week states.
- Packet-local observability review MUST NOT claim canonical Today/Week ownership for this slice.
- `degraded-but-expected` is acceptable only when the missing or noisy evidence is unrelated to the Week helper and the Week visual/request identifiers remain attributable.

Architect slice directory: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean`
