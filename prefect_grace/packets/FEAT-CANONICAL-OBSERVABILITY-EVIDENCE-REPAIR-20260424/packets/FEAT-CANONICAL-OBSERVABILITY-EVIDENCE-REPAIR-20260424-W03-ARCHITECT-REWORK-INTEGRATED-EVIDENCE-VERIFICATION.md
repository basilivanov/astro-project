# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-ARCHITECT-REWORK-INTEGRATED-EVIDENCE-VERIFICATION

## Title
Architect Rework Integrated Evidence Verification

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-ARCHITECT-REWORK-INTEGRATED-EVIDENCE-VERIFICATION`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: wave-final today-week review returned FAIL_NO_EVIDENCE; Today and Week canonical flows have zero recent records; Admin watcher reports no success events; Catalog watcher reports stale success evidence; green tests do not satisfy canonical observability evidence gate

## Wave
W03

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`.
- Reviewer packet `FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REVIEW-INTEGRATED-EVIDENCE-CLOSEOUT`.
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
  - prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REVIEW-INTEGRATED-EVIDENCE-CLOSEOUT

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
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-ARCHITECT-REWORK-INTEGRATED-EVIDENCE-VERIFICATION",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W03",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Integrated Evidence Verification",
  "summary": "Review reviewer blockers for FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: wave-final today-week review returned FAIL_NO_EVIDENCE; Today and Week canonical flows have zero recent records; Admin watcher reports no success events; Catalog watcher reports stale success evidence; green tests do not satisfy canonical observability evidence gate",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`.",
    "Reviewer packet `FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REVIEW-INTEGRATED-EVIDENCE-CLOSEOUT`.",
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
      "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**"
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
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REVIEW-INTEGRATED-EVIDENCE-CLOSEOUT"
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
  "parent_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
