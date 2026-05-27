# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-EVIDENCE

## Title
Verifier Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-EVIDENCE`

## Packet Type
execution

## Summary
Validate the coder packet with the required test profile and observability gate.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR
- coder packet file

## Acceptance Criteria
- Commands run are recorded.
- Evidence paths are recorded.
- Observability verdict is explicit.
- Frontend visual verdict is explicit when UI is touched.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - logs/**
  - artifacts/**
  - prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR/**
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR

## Notes
- Fail the packet if evidence is missing.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Evidence",
  "summary": "Validate the coder packet with the required test profile and observability gate.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
    "coder packet file"
  ],
  "acceptance_criteria": [
    "Commands run are recorded.",
    "Evidence paths are recorded.",
    "Observability verdict is explicit.",
    "Frontend visual verdict is explicit when UI is touched."
  ],
  "verification_profile": {
    "backend": "execute minimally sufficient backend profile",
    "frontend": "execute minimally sufficient frontend profile if UI is touched",
    "observability": "mandatory log, replay, digest, and trace review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "frontend_profile": null,
    "frontend_commands": [],
    "observability_profile": "read-only",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ],
    "observability_scope": "packet_local",
    "canonical_flow_commands": [],
    "touches_frontend": true,
    "requires_frontend_visual": true,
    "artifact_globs": [
      "logs/**",
      "artifacts/**",
      "prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR/**"
    ],
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "No green-only pass without evidence review.",
    "Blocking issues are explicit when evidence is missing."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR"
  ],
  "notes": [
    "Fail the packet if evidence is missing."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
