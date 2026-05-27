# Packet: FEAT-REWORK-HINTS-W00-ARCHITECT-FORMALIZATION

## Title
Architect Formalization

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W00`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W00:packet:FEAT-REWORK-HINTS-W00-ARCHITECT-FORMALIZATION`

## Packet Type
execution

## Summary
Formalize the business feature into compact packet-first GRACE artifacts and define execution boundaries.

## Wave
W00

## Role
architect

## Reasoning
xhigh

## Parent Packet
-

## Review Target
-

## Write Scope
- Feature-local packet-first artifacts for this feature.
- Impacted sections of core GRACE documents only when root_deltas require them.

## Inputs
- FEAT-REWORK-HINTS-W00-CANON-DIGEST
- Feature brief `FEAT-REWORK-HINTS/feature-brief.md`.
- Compact business context and directly relevant repository baseline.

## Acceptance Criteria
- Goal, waves, bounded scopes, packet list, and next action are explicit.
- Architect produces packet-first artifacts by default.
- Open decisions are separated from execution-ready facts.
- Wave plan reflects every wave represented by packet candidates.

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review and consistency check

## Execution Hints
- sandbox: danger-full-access

## Reviewer Gate
- No missing artifact delta for impacted surfaces.
- No silent scope expansion.

## Dependencies
- FEAT-REWORK-HINTS-W00-CANON-DIGEST

## Notes
- Use canon-digest.md as advisory project memory; verify any critical boundary against live files before slicing.
- Do not materialize local GRACE slice docs unless explicitly requested with real root_deltas.
- Write feature brief, wave plan, execution packet, and architect manifest before direct execution.
- Keep frontend verification explicit if UI is touched.
- Return FINAL_ARCHITECT_ARTIFACT_PLAN_JSON markers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W00-ARCHITECT-FORMALIZATION",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W00",
  "packet_type": "execution",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Formalization",
  "summary": "Formalize the business feature into compact packet-first GRACE artifacts and define execution boundaries.",
  "write_scope": [
    "Feature-local packet-first artifacts for this feature.",
    "Impacted sections of core GRACE documents only when root_deltas require them."
  ],
  "inputs": [
    "FEAT-REWORK-HINTS-W00-CANON-DIGEST",
    "Feature brief `FEAT-REWORK-HINTS/feature-brief.md`.",
    "Compact business context and directly relevant repository baseline."
  ],
  "acceptance_criteria": [
    "Goal, waves, bounded scopes, packet list, and next action are explicit.",
    "Architect produces packet-first artifacts by default.",
    "Open decisions are separated from execution-ready facts.",
    "Wave plan reflects every wave represented by packet candidates."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "artifact review and consistency check"
  },
  "execution_hints": {
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No missing artifact delta for impacted surfaces.",
    "No silent scope expansion."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-W00-CANON-DIGEST"
  ],
  "notes": [
    "Use canon-digest.md as advisory project memory; verify any critical boundary against live files before slicing.",
    "Do not materialize local GRACE slice docs unless explicitly requested with real root_deltas.",
    "Write feature brief, wave plan, execution packet, and architect manifest before direct execution.",
    "Keep frontend verification explicit if UI is touched.",
    "Return FINAL_ARCHITECT_ARTIFACT_PLAN_JSON markers."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
