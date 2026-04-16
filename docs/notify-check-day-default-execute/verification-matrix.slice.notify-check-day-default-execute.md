# Notify check Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-FEAT-NOTIFY-CHECK`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-FEAT-NOTIFY-CHECK-BINDING-PROBE` | `SCN-FEAT-NOTIFY-CHECK-BINDING-PROBE` | test -f docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md; test -f docs/notify-check-day-default-execute/EXECUTION_PACKET.md | Feature-local docs exist and record concrete Day runtime-indicator bindings before any behavior edit is attempted. |
| `VM-FEAT-NOTIFY-CHECK-CONTRACT-MISMATCH` | `SCN-FEAT-NOTIFY-CHECK-CONTRACT-MISMATCH` | rg -n --hidden -S "notify check|notify-check|notifyCheck|notify_check|execute=true|execute false" frontend/app frontend/components frontend/lib frontend/e2e | Worker can point to exact repo evidence showing whether a Day Notify-check intake/default/dispatch surface exists. If absent, the verdict is contract-mismatch-no-day-notify-surface. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- Frontend changes MUST include visual evidence when UI is touched.
- Post-test observability review is mandatory when the slice touches Today, Week, Admin, Catalog, or Billing.

Architect slice directory: `/opt/astro-project/docs/notify-check-day-default-execute`
