# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION

## Title
Repair Today/Week Post-Test Classification

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W01`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W01:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION`

## Packet Type
execution

## Summary
Update tools/post_test_review.py and tests so concrete degraded Today/Week evidence is classified as degradation rather than no-evidence.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION`

## Write Scope
- tools/post_test_review.py
- tests/test_post_test_review.py
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**

## Inputs
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W00-ARCHITECT-FORMALIZATION
- feature brief
- current tools/post_test_review.py
- tests/test_post_test_review.py

## Acceptance Criteria
- Identifier-bearing degraded evidence cannot produce no-evidence-blocker.
- Today auth/text degradation produces unexpected-degradation unless stable expected reason code is approved.
- Week fallback/degradation exposes stable reason codes and correct degradation classification.
- True missing evidence remains no-evidence-blocker.

## Verification Profile
- backend: python3 -m pytest tests/test_post_test_review.py
- frontend: not required
- observability: packet_local: python3 tools/post_test_review.py --profile today-week --since 30m --report-format md

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No product behavior changes.
- No degraded behavior hidden as clean.
- Tests demonstrate regression against FAIL_NO_EVIDENCE misclassification.

## Dependencies
-

## Notes
- Do not touch frontend.
- Preserve existing verdict vocabulary.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Repair Today/Week Post-Test Classification",
  "summary": "Update tools/post_test_review.py and tests so concrete degraded Today/Week evidence is classified as degradation rather than no-evidence.",
  "write_scope": [
    "tools/post_test_review.py",
    "tests/test_post_test_review.py",
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**"
  ],
  "inputs": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "current tools/post_test_review.py",
    "tests/test_post_test_review.py"
  ],
  "acceptance_criteria": [
    "Identifier-bearing degraded evidence cannot produce no-evidence-blocker.",
    "Today auth/text degradation produces unexpected-degradation unless stable expected reason code is approved.",
    "Week fallback/degradation exposes stable reason codes and correct degradation classification.",
    "True missing evidence remains no-evidence-blocker."
  ],
  "verification_profile": {
    "backend": "python3 -m pytest tests/test_post_test_review.py",
    "frontend": "not required",
    "observability": "packet_local: python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No product behavior changes.",
    "No degraded behavior hidden as clean.",
    "Tests demonstrate regression against FAIL_NO_EVIDENCE misclassification."
  ],
  "dependencies": [],
  "notes": [
    "Do not touch frontend.",
    "Preserve existing verdict vocabulary."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
