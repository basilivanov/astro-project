# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT

## Title
Verify W03 Report Workflow Split

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT`

## Packet Type
execution

## Summary
Verify W03 report workflow behavior, report_workflow file limits, targeted report tests, and wave_final evidence.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION`

## Write Scope
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION

## Acceptance Criteria
- W03 commands pass
- report_workflow.py and extracted modules are <=1000 lines
- Report/Week evidence verdict is clean

## Verification Profile
- backend: W03 targeted report commands
- frontend: not required
- observability: wave_final clean required

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
- Evidence includes lifecycle tests, size output, and post-test trace verdict

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION

## Notes
- W03 owns canonical report workflow emitter evidence.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Verify W03 Report Workflow Split",
  "summary": "Verify W03 report workflow behavior, report_workflow file limits, targeted report tests, and wave_final evidence.",
  "write_scope": [
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION"
  ],
  "acceptance_criteria": [
    "W03 commands pass",
    "report_workflow.py and extracted modules are <=1000 lines",
    "Report/Week evidence verdict is clean"
  ],
  "verification_profile": {
    "backend": "W03 targeted report commands",
    "frontend": "not required",
    "observability": "wave_final clean required"
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
    "Evidence includes lifecycle tests, size output, and post-test trace verdict"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION"
  ],
  "notes": [
    "W03 owns canonical report workflow emitter evidence."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
