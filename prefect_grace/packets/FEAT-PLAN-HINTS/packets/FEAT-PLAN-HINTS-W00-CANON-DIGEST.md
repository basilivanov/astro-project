# Packet: FEAT-PLAN-HINTS-W00-CANON-DIGEST

## Title
Canon Digest

## GRACE IDs
- feature_ref: `feature:FEAT-PLAN-HINTS`
- wave_ref: `feature:FEAT-PLAN-HINTS:wave:W00`
- packet_ref: `feature:FEAT-PLAN-HINTS:wave:W00:packet:FEAT-PLAN-HINTS-W00-CANON-DIGEST`

## Packet Type
execution

## Summary
Read the project GRACE canon and produce a compact architect-ready digest for this feature.

## Wave
W00

## Role
canon_digest

## Reasoning
medium

## Parent Packet
-

## Review Target
-

## Write Scope
- FEAT-PLAN-HINTS/canon-digest.md

## Inputs
- Feature brief `FEAT-PLAN-HINTS/feature-brief.md`.
- Root GRACE canon documents and recent slice manifests supplied in context.

## Acceptance Criteria
- Digest is compact, source-linked, and architect-ready.
- Digest does not create waves, packets, or architecture decisions.
- Digest preserves important filenames, anchors, invariants, and verification gates.

## Verification Profile
- backend: not required
- frontend: not required
- observability: not required

## Execution Hints
- canon_digest_output_path: /opt/astro-project/prefect_grace/packets/FEAT-PLAN-HINTS/canon-digest.md

## Reviewer Gate
- Digest is advisory context only; architect remains source of slicing decisions.

## Dependencies
-

## Notes
- Output Markdown only.
- Keep output bounded to roughly 8K-12K tokens.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-PLAN-HINTS-W00-CANON-DIGEST",
  "feature_id": "FEAT-PLAN-HINTS",
  "wave_id": "W00",
  "packet_type": "execution",
  "role": "canon_digest",
  "reasoning": "medium",
  "title": "Canon Digest",
  "summary": "Read the project GRACE canon and produce a compact architect-ready digest for this feature.",
  "write_scope": [
    "FEAT-PLAN-HINTS/canon-digest.md"
  ],
  "inputs": [
    "Feature brief `FEAT-PLAN-HINTS/feature-brief.md`.",
    "Root GRACE canon documents and recent slice manifests supplied in context."
  ],
  "acceptance_criteria": [
    "Digest is compact, source-linked, and architect-ready.",
    "Digest does not create waves, packets, or architecture decisions.",
    "Digest preserves important filenames, anchors, invariants, and verification gates."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "not required"
  },
  "execution_hints": {
    "canon_digest_output_path": "/opt/astro-project/prefect_grace/packets/FEAT-PLAN-HINTS/canon-digest.md"
  },
  "reviewer_gate": [
    "Digest is advisory context only; architect remains source of slicing decisions."
  ],
  "dependencies": [],
  "notes": [
    "Output Markdown only.",
    "Keep output bounded to roughly 8K-12K tokens."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
