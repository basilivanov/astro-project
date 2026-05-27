# Packet: FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W02-VERIFY-W03-CLOSEOUT-EVIDENCE

## Title
Verify W03 Closeout Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424`
- wave_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W02`
- packet_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W02:packet:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W02-VERIFY-W03-CLOSEOUT-EVIDENCE`

## Packet Type
execution

## Summary
Run generation first, then Today/Week, read-only, Admin, and Catalog watcher commands and store evidence.

## Wave
W02

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-ARCHITECT-GATE-W01`

## Write Scope
- prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W02/**

## Inputs
- architect_w01_gate accepted
- generation command

## Acceptance Criteria
- Generation command is run before all watcher commands.
- Post-test review no longer returns `FAIL_NO_EVIDENCE` immediately after generation.
- Admin and Catalog watcher outputs include fresh success evidence or precise expected blockers.
- Evidence includes timestamps and identifiers for each flow.

## Verification Profile
- backend: not required unless W01 changed after gate
- frontend: not required
- observability: wave_final canonical command sequence

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
- Evidence order is generation before review.
- All commands and verdicts are captured.

## Dependencies
- FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-ARCHITECT-GATE-W01

## Notes
- `degraded-but-expected` is acceptable only with explicit accepted reason codes or precise blocker context.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W02-VERIFY-W03-CLOSEOUT-EVIDENCE",
  "feature_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify W03 Closeout Evidence",
  "summary": "Run generation first, then Today/Week, read-only, Admin, and Catalog watcher commands and store evidence.",
  "write_scope": [
    "prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/evidence/W02/**"
  ],
  "inputs": [
    "architect_w01_gate accepted",
    "generation command"
  ],
  "acceptance_criteria": [
    "Generation command is run before all watcher commands.",
    "Post-test review no longer returns `FAIL_NO_EVIDENCE` immediately after generation.",
    "Admin and Catalog watcher outputs include fresh success evidence or precise expected blockers.",
    "Evidence includes timestamps and identifiers for each flow."
  ],
  "verification_profile": {
    "backend": "not required unless W01 changed after gate",
    "frontend": "not required",
    "observability": "wave_final canonical command sequence"
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
    "Evidence order is generation before review.",
    "All commands and verdicts are captured."
  ],
  "dependencies": [
    "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-ARCHITECT-GATE-W01"
  ],
  "notes": [
    "`degraded-but-expected` is acceptable only with explicit accepted reason codes or precise blocker context."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-ARCHITECT-GATE-W01",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
