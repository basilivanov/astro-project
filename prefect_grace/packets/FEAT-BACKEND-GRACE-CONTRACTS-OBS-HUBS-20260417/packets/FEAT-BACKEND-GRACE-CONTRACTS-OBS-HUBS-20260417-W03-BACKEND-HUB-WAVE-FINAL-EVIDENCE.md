# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W03-BACKEND-HUB-WAVE-FINAL-EVIDENCE

## Title
Backend Hub Wave Final Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W03:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W03-BACKEND-HUB-WAVE-FINAL-EVIDENCE`

## Packet Type
execution

## Summary
Run final backend verification and canonical today-week observability closeout.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W03-BACKEND-HUB-WAVE-FINAL-EVIDENCE`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence/**

## Inputs
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-ARCHITECT-W02-GATE
- execution packet
- architect manifest

## Acceptance Criteria
- Canonical flow commands run before today-week review.
- Backend quick and targeted pytest results are recorded.
- Final observability verdict is clean or degraded-but-expected, or blocks with explicit reason.

## Verification Profile
- backend: backend:quick plus full targeted hub pytest bundle
- frontend: not required
- observability: python3 tools/post_test_review.py --profile today-week --since 30m --report-format md; observability_scope=wave_final

## Execution Hints
- workdir: /opt/astro-project
- runner: codex
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Do not treat green tests alone as acceptance.
- Block unexpected-degradation and no-evidence-blocker.

## Dependencies
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-ARCHITECT-W02-GATE

## Notes
- degraded-but-expected requires explicit rationale.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W03-BACKEND-HUB-WAVE-FINAL-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Backend Hub Wave Final Evidence",
  "summary": "Run final backend verification and canonical today-week observability closeout.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/evidence/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-ARCHITECT-W02-GATE",
    "execution packet",
    "architect manifest"
  ],
  "acceptance_criteria": [
    "Canonical flow commands run before today-week review.",
    "Backend quick and targeted pytest results are recorded.",
    "Final observability verdict is clean or degraded-but-expected, or blocks with explicit reason."
  ],
  "verification_profile": {
    "backend": "backend:quick plus full targeted hub pytest bundle",
    "frontend": "not required",
    "observability": "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md; observability_scope=wave_final"
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
    "Do not treat green tests alone as acceptance.",
    "Block unexpected-degradation and no-evidence-blocker."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W02-ARCHITECT-W02-GATE"
  ],
  "notes": [
    "degraded-but-expected requires explicit rationale."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W03-BACKEND-HUB-WAVE-FINAL-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
