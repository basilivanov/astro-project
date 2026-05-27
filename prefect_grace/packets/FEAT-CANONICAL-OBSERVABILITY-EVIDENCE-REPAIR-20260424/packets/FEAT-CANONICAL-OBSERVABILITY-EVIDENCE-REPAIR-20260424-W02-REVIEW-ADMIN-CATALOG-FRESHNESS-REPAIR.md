# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REVIEW-ADMIN-CATALOG-FRESHNESS-REPAIR

## Title
Review Admin/Catalog Freshness Repair

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W02`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W02:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REVIEW-ADMIN-CATALOG-FRESHNESS-REPAIR`

## Packet Type
execution

## Summary
Review W02 watcher changes and verifier evidence for provenance correctness.

## Wave
W02

## Role
reviewer

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS`

## Write Scope
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**

## Inputs
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS

## Acceptance Criteria
- Reviewer confirms stale, missing, and degraded Admin/Catalog evidence are distinguishable.
- Reviewer confirms no product behavior changes.
- Reviewer identifies producer-fix need only if evidence proves watcher repair is insufficient.

## Verification Profile
- backend: evidence review only
- frontend: not required
- observability: evidence review only

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Self-review complete.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS

## Notes
- Route bounded producer rework only with concrete evidence.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REVIEW-ADMIN-CATALOG-FRESHNESS-REPAIR",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "reviewer",
  "reasoning": "high",
  "title": "Review Admin/Catalog Freshness Repair",
  "summary": "Review W02 watcher changes and verifier evidence for provenance correctness.",
  "write_scope": [
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**"
  ],
  "inputs": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS",
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS"
  ],
  "acceptance_criteria": [
    "Reviewer confirms stale, missing, and degraded Admin/Catalog evidence are distinguishable.",
    "Reviewer confirms no product behavior changes.",
    "Reviewer identifies producer-fix need only if evidence proves watcher repair is insufficient."
  ],
  "verification_profile": {
    "backend": "evidence review only",
    "frontend": "not required",
    "observability": "evidence review only"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "Self-review complete."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-VERIFY-ADMIN-CATALOG-WATCHERS"
  ],
  "notes": [
    "Route bounded producer rework only with concrete evidence."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-REPAIR-ADMIN-CATALOG-FRESHNESS-WATCHERS",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
