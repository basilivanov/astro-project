# Packet: FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-VERIFIER-EVIDENCE

## Title
Verifier Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ`
- wave_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:wave:W02:packet:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-VERIFIER-EVIDENCE`

## Packet Type
execution

## Summary
Validate the W02 dev-observability implementation with the packet-local backend and observability lanes.

## Wave
W02

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
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-LIVE-IMPLEMENTATION-PACKET
- `/opt/astro-project/docs/backend-grace-observability-wave-tz/verification-matrix.slice.backend-grace-observability-wave-tz.md`

## Acceptance Criteria
- Exact commands, PASS or FAIL result, and evidence paths are recorded.
- Observability verdict is explicit and limited to `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.
- Any scheduler or analytics non-emission is classified explicitly.

## Verification Profile
- backend: execute `backend:quick` and the targeted backend active-slice pytest bundle
- frontend: not required
- observability: execute packet-local `read-only` post-test review

## Execution Hints
- workdir: /opt/astro-project
- runner: codex
- backend_profile: backend_quick
- observability_scope: packet_local
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md

## Reviewer Gate
- No green-only pass without evidence review.
- Missing or fragmented evidence must block acceptance.

## Dependencies
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-LIVE-IMPLEMENTATION-PACKET

## Notes
- This packet may accept `degraded-but-expected` only when the reason is explicit and packet-local.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-VERIFIER-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Evidence",
  "summary": "Validate the W02 dev-observability implementation with the packet-local backend and observability lanes.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-LIVE-IMPLEMENTATION-PACKET",
    "/opt/astro-project/docs/backend-grace-observability-wave-tz/verification-matrix.slice.backend-grace-observability-wave-tz.md"
  ],
  "acceptance_criteria": [
    "Exact commands, PASS or FAIL result, and evidence paths are recorded.",
    "Observability verdict is explicit and limited to clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker.",
    "Any scheduler or analytics non-emission is classified explicitly."
  ],
  "verification_profile": {
    "backend": "execute backend:quick and the targeted backend active-slice pytest bundle",
    "frontend": "not required",
    "observability": "execute packet-local read-only post-test review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_scope": "packet_local",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ]
  },
  "reviewer_gate": [
    "No green-only pass without evidence review.",
    "Missing or fragmented evidence must block acceptance."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-LIVE-IMPLEMENTATION-PACKET"
  ],
  "notes": [
    "This packet may accept degraded-but-expected only when the reason is explicit and packet-local."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
