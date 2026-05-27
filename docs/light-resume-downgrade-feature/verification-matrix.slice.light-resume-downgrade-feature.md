# Light resume downgrade feature Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-LIGHT-RESUME-DOWNGRADE`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-SLICE-MAIN` | `SLICE-FEAT-LIGHT-RESUME-DOWNGRADE` | - | Light resume downgrade feature |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/light-resume-downgrade-feature`
