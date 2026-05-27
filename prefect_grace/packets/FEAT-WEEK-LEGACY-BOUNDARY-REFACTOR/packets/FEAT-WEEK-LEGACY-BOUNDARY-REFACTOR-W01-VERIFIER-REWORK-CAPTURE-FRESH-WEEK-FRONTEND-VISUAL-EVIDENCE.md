# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Title
Verifier Rework Capture Fresh Week Frontend Visual Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to narrow packet-local write scope
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
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Capture Fresh Week Frontend Visual Evidence",
  "summary": "Validate the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-VERDICT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "execute minimally sufficient backend profile",
    "frontend": "execute minimally sufficient frontend profile if UI is touched",
    "observability": "mandatory log, replay, digest, and trace review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to narrow packet-local write scope",
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
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
