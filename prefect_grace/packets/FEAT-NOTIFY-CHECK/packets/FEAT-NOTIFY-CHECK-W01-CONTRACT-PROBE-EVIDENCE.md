# Packet: FEAT-NOTIFY-CHECK-W01-CONTRACT-PROBE-EVIDENCE

## Title
Contract Probe Evidence

## Packet Type
execution

## Summary
Verify whether the current repo contains a Day-owned Notify-check intake/default/dispatch surface and record packet-local evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- prefect_grace/packets/FEAT-NOTIFY-CHECK/**

## Inputs
- FEAT-NOTIFY-CHECK-W00-ARCHITECT-FORMALIZATION
- FEAT-NOTIFY-CHECK-W01-REPO-FILE-BINDING-PACKET
- /opt/astro-project/docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/notify-check-day-default-execute/EXECUTION_PACKET.md

## Acceptance Criteria
- Exact commands and PASS/FAIL are recorded.
- Evidence states whether a Day-owned Notify-check intake/default/dispatch file exists.
- If absent, verdict is `contract-mismatch-no-day-notify-surface`.
- Runtime-indicator-only evidence is explicitly marked adjacent and not acceptance proof.

## Verification Profile
- backend: not required; backend is frozen.
- frontend: targeted repository scan only; do not run Day runtime Playwright as Notify-check proof.
- observability: packet_local; no canonical Today/Week closeout; degraded-but-expected is acceptable for documented contract mismatch.
- execution: {'backend_commands': [], 'frontend_commands': ['rg -n --hidden -S "notify check|notify-check|notifyCheck|notify_check|execute=true|execute false" frontend/app frontend/components frontend/lib frontend/e2e'], 'observability_commands': ['test -f docs/notify-check-day-default-execute/ARCHITECT_HANDOFF.md', 'test -f docs/notify-check-day-default-execute/EXECUTION_PACKET.md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['prefect_grace/packets/FEAT-NOTIFY-CHECK/**', 'docs/notify-check-day-default-execute/**']}

## Reviewer Gate
- Reject if the verifier claims Notify-check acceptance from `frontend/e2e/day-dev-indicator.spec.ts`.
- Reject if backend, Prefect, or frontend behavior files are modified.
- Accept a `degraded-but-expected` verdict only when the degradation is the documented contract mismatch.

## Dependencies
- FEAT-NOTIFY-CHECK-W01-REPO-FILE-BINDING-PACKET

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-NOTIFY-CHECK-W01-CONTRACT-PROBE-EVIDENCE",
  "feature_id": "FEAT-NOTIFY-CHECK",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "title": "Contract Probe Evidence",
  "summary": "Verify whether the current repo contains a Day-owned Notify-check intake/default/dispatch surface and record packet-local evidence.",
  "write_scope": [
    "prefect_grace/packets/FEAT-NOTIFY-CHECK/**"
  ],
  "verification_profile": {
    "backend": "not required; backend is frozen",
    "frontend": "targeted repository scan only",
    "observability": "packet_local; no canonical Today/Week closeout; degraded-but-expected is acceptable for documented contract mismatch"
  }
}
END_FINAL_PACKET_CONTRACT_JSON
