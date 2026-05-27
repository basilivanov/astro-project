# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-REWORK-VERIFY-W02-API-GATEWAY-SPLIT

## Title
Architect Rework Verify W02 API Gateway Split

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-REWORK-VERIFY-W02-API-GATEWAY-SPLIT`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: W02 backend tests and size checks passed; W02 wave-final observability evidence is not clean; Today flow has no-evidence-blocker; Week flow has unexpected degradation; Admin and Catalog evidence is stale for this verification

## Wave
W02

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`.
- Reviewer packet `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEW-W02-API-GATEWAY-SPLIT`.
- Reviewer blocker notes and latest verifier evidence.

## Acceptance Criteria
- Architect classifies the blocker as self-resolvable, requires_user_decision, or requires_planner.
- If self-resolvable, architect returns a bounded direct rework packet for coder.
- If escalation is required, architect states the narrowest blocking reason.

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- artifact_globs:
  - logs/*.jsonl
  - test-results/**/*.json
  - test-results/**/*.md
  - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEW-W02-API-GATEWAY-SPLIT

## Notes
- Return FINAL_DIRECT_REWORK_PACKET_JSON.
- Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.
- Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.
- Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.
- Use rework_mode=decision_required when the blocker should not resume coder work directly.
- Use requires_user_decision only for true business/product/user decisions.
- Use requires_planner only when packet graph or decomposition must change.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-ARCHITECT-REWORK-VERIFY-W02-API-GATEWAY-SPLIT",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Verify W02 API Gateway Split",
  "summary": "Review reviewer blockers for FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: W02 backend tests and size checks passed; W02 wave-final observability evidence is not clean; Today flow has no-evidence-blocker; Week flow has unexpected degradation; Admin and Catalog evidence is stale for this verification",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`.",
    "Reviewer packet `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEW-W02-API-GATEWAY-SPLIT`.",
    "Reviewer blocker notes and latest verifier evidence."
  ],
  "acceptance_criteria": [
    "Architect classifies the blocker as self-resolvable, requires_user_decision, or requires_planner.",
    "If self-resolvable, architect returns a bounded direct rework packet for coder.",
    "If escalation is required, architect states the narrowest blocking reason."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "artifact review only"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ],
    "artifact_globs": [
      "logs/*.jsonl",
      "test-results/**/*.json",
      "test-results/**/*.md",
      "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/**"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEW-W02-API-GATEWAY-SPLIT"
  ],
  "notes": [
    "Return FINAL_DIRECT_REWORK_PACKET_JSON.",
    "Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.",
    "Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.",
    "Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.",
    "Use rework_mode=decision_required when the blocker should not resume coder work directly.",
    "Use requires_user_decision only for true business/product/user decisions.",
    "Use requires_planner only when packet graph or decomposition must change."
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
