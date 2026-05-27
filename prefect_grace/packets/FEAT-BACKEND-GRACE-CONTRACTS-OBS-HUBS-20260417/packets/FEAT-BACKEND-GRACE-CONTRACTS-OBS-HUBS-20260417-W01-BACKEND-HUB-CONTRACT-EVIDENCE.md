# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-EVIDENCE

## Title
Backend Hub Contract Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-EVIDENCE`

## Packet Type
execution

## Summary
Run W01 backend and packet-local observability evidence.

## Wave
W01

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence/**

## Inputs
- coder_contracts output
- execution packet
- architect manifest

## Acceptance Criteria
- All required commands are recorded with PASS or FAIL.
- Packet-local evidence is clean or degraded-but-expected.
- Unexpected-degradation and no-evidence-blocker block the wave.

## Verification Profile
- backend: backend:quick plus targeted hub pytest bundle
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
- No skipped command without blocker.
- Evidence includes relevant trace_id or correlation_id when present.

## Dependencies
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT

## Notes
- Does not own canonical today-week closeout.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Backend Hub Contract Evidence",
  "summary": "Run W01 backend and packet-local observability evidence.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence/**"
  ],
  "inputs": [
    "coder_contracts output",
    "execution packet",
    "architect manifest"
  ],
  "acceptance_criteria": [
    "All required commands are recorded with PASS or FAIL.",
    "Packet-local evidence is clean or degraded-but-expected.",
    "Unexpected-degradation and no-evidence-blocker block the wave."
  ],
  "verification_profile": {
    "backend": "backend:quick plus targeted hub pytest bundle",
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
    "No skipped command without blocker.",
    "Evidence includes relevant trace_id or correlation_id when present."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT"
  ],
  "notes": [
    "Does not own canonical today-week closeout."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
