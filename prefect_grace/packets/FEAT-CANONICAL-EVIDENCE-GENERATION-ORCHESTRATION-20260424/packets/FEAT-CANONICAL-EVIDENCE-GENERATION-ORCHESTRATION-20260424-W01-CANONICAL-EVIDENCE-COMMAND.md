# Packet: FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND

## Title
Canonical Evidence Command

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424`
- wave_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01`
- packet_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01:packet:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND`

## Packet Type
execution

## Summary
Implement `scripts/generate_canonical_evidence.py` and targeted tests for deterministic Today, Week, Admin, and Catalog evidence generation.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
-

## Write Scope
- scripts/generate_canonical_evidence.py
- tests/test_canonical_evidence_generation.py
- tests/test_post_test_review.py
- tests/test_log_watch_feed_admin.py
- tests/test_forecast_catalog_watch.py
- tools/post_test_review.py only for minimal adapter if strictly required
- tools/log_watch/*.py only for minimal hook support if strictly required

## Inputs
- FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W00-ARCHITECT-FORMALIZATION
- feature brief
- tools/post_test_review.py
- tools/log_watch/feed_admin_watch.py
- tools/log_watch/forecast_catalog_watch.py
- backend/app/logging_utils.py
- existing Today/Week/Admin/Catalog producer tests

## Acceptance Criteria
- Command emits all four canonical flow evidences inside the current review window.
- Command uses existing backend producer/logging contracts rather than direct fabricated watcher pass records.
- Records include timestamps plus trace/request/correlation/report/provenance identifiers.
- Targeted tests cover successful fresh generation and stale/missing failure behavior.
- No strict watcher verdict rules are weakened.

## Verification Profile
- backend: targeted pytest plus `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- frontend: not required
- observability: packet_local generation logs; `degraded-but-expected` acceptable only with explicit reason codes

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No fabricated direct JSONL pass payloads.
- No parser/reviewer strictness weakening.
- Command name and verifier usage are documented in packet evidence.

## Dependencies
-

## Notes
- Prefer invoking existing router/service producer paths with deterministic stubs/mocks where needed.
- If live credentials are required, stop and report blocker instead of fabricating canonical evidence.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND",
  "feature_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Canonical Evidence Command",
  "summary": "Implement `scripts/generate_canonical_evidence.py` and targeted tests for deterministic Today, Week, Admin, and Catalog evidence generation.",
  "write_scope": [
    "scripts/generate_canonical_evidence.py",
    "tests/test_canonical_evidence_generation.py",
    "tests/test_post_test_review.py",
    "tests/test_log_watch_feed_admin.py",
    "tests/test_forecast_catalog_watch.py",
    "tools/post_test_review.py only for minimal adapter if strictly required",
    "tools/log_watch/*.py only for minimal hook support if strictly required"
  ],
  "inputs": [
    "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "tools/post_test_review.py",
    "tools/log_watch/feed_admin_watch.py",
    "tools/log_watch/forecast_catalog_watch.py",
    "backend/app/logging_utils.py",
    "existing Today/Week/Admin/Catalog producer tests"
  ],
  "acceptance_criteria": [
    "Command emits all four canonical flow evidences inside the current review window.",
    "Command uses existing backend producer/logging contracts rather than direct fabricated watcher pass records.",
    "Records include timestamps plus trace/request/correlation/report/provenance identifiers.",
    "Targeted tests cover successful fresh generation and stale/missing failure behavior.",
    "No strict watcher verdict rules are weakened."
  ],
  "verification_profile": {
    "backend": "targeted pytest plus `docker exec astro-project-backend-1 python3 scripts/pipeline.py`",
    "frontend": "not required",
    "observability": "packet_local generation logs; `degraded-but-expected` acceptable only with explicit reason codes"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No fabricated direct JSONL pass payloads.",
    "No parser/reviewer strictness weakening.",
    "Command name and verifier usage are documented in packet evidence."
  ],
  "dependencies": [],
  "notes": [
    "Prefer invoking existing router/service producer paths with deterministic stubs/mocks where needed.",
    "If live credentials are required, stop and report blocker instead of fabricating canonical evidence."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
