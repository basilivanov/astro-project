# Packet: FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND

## Title
Verify Evidence Command

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424`
- wave_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01`
- packet_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01:packet:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND`

## Packet Type
execution

## Summary
Run targeted command tests, backend quick pipeline, and packet-local evidence inspection for W01.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND`

## Write Scope
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/**

## Inputs
- coder_w01_evidence_command output

## Acceptance Criteria
- Generation command runs successfully.
- Targeted tests pass.
- Backend quick pipeline passes or unrelated failures are explicitly isolated.
- Packet-local logs show fresh records and identifiers for all four flows.

## Verification Profile
- backend: `python3 -m pytest tests/test_canonical_evidence_generation.py tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- frontend: not required
- observability: packet_local; inspect generated JSONL records and report verdict clean/degraded-but-expected/unexpected/no-evidence

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
  - prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence includes command output and sampled log records.
- Verdict is explicit.

## Dependencies
- FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND

## Notes
- Do not run full frontend E2E.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND",
  "feature_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify Evidence Command",
  "summary": "Run targeted command tests, backend quick pipeline, and packet-local evidence inspection for W01.",
  "write_scope": [
    "prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W01/**"
  ],
  "inputs": [
    "coder_w01_evidence_command output"
  ],
  "acceptance_criteria": [
    "Generation command runs successfully.",
    "Targeted tests pass.",
    "Backend quick pipeline passes or unrelated failures are explicitly isolated.",
    "Packet-local logs show fresh records and identifiers for all four flows."
  ],
  "verification_profile": {
    "backend": "`python3 -m pytest tests/test_canonical_evidence_generation.py tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py` and `docker exec astro-project-backend-1 python3 scripts/pipeline.py`",
    "frontend": "not required",
    "observability": "packet_local; inspect generated JSONL records and report verdict clean/degraded-but-expected/unexpected/no-evidence"
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
      "prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/**"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence includes command output and sampled log records.",
    "Verdict is explicit."
  ],
  "dependencies": [
    "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND"
  ],
  "notes": [
    "Do not run full frontend E2E."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
