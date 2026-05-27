# Expandable dev indicator pipeline check Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-DEV-RUNTIME-INDICATOR-PIPELINE-CHECK`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-SLICE-MAIN` | `SLICE-FEAT-DEV-RUNTIME-INDICATOR-PIPELINE-CHECK` | - | Expandable dev indicator pipeline check |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/expandable-dev-indicator-pipeline-check`
