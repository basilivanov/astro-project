# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-EVIDENCE

## Title
Backend Hub Observability Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W02:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-EVIDENCE`

## Packet Type
execution

## Summary
Run W02 backend/tooling verification and packet-local observability evidence.

## Wave
W02

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence/**

## Inputs
- coder_observability output
- execution packet
- architect manifest

## Acceptance Criteria
- Required backend and tooling tests are recorded.
- Packet-local review is clean or degraded-but-expected.
- Evidence names surfaced hub landmarks or exact remaining gap.

## Verification Profile
- backend: backend:quick plus logging/tooling pytest bundle
- frontend: not required
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md

## Execution Hints
- workdir: /opt/astro-project
- runner: codex
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Reject if module/fn/block readability is still absent.

## Dependencies
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT

## Notes
- Does not own canonical today-week closeout.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Backend Hub Observability Evidence",
  "summary": "Run W02 backend/tooling verification and packet-local observability evidence.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence/**"
  ],
  "inputs": [
    "coder_observability output",
    "execution packet",
    "architect manifest"
  ],
  "acceptance_criteria": [
    "Required backend and tooling tests are recorded.",
    "Packet-local review is clean or degraded-but-expected.",
    "Evidence names surfaced hub landmarks or exact remaining gap."
  ],
  "verification_profile": {
    "backend": "backend:quick plus logging/tooling pytest bundle",
    "frontend": "not required",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Reject if module/fn/block readability is still absent."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT"
  ],
  "notes": [
    "Does not own canonical today-week closeout."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-BACKEND-HUB-OBSERVABILITY-ALIGNMENT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
