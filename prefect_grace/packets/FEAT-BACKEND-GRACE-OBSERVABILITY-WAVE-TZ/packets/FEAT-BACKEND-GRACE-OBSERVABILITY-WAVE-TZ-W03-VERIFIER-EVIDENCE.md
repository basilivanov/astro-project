# Packet: FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE

## Title
Verifier Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ`
- wave_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:wave:W03:packet:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE`

## Packet Type
execution

## Summary
Run the final canonical backend and `today-week` observability lanes for the completed backend active slice and record the explicit closeout verdict.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-ARCHITECT-WAVE-GATE
- `/opt/astro-project/docs/backend-grace-observability-wave-tz/verification-matrix.slice.backend-grace-observability-wave-tz.md`

## Acceptance Criteria
- backend:quick command passes or failure is attached with exact failing test and traceback summary.
- Targeted backend active-slice pytest command passes or failure is attached with exact failing test and traceback summary.
- Final `today-week` post-test review completes and yields an explicit `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker` verdict.
- If observability evidence is absent, fragmented, or unexpectedly degraded, verifier blocks acceptance.

## Verification Profile
- backend: execute `backend:quick` and the targeted backend active-slice pytest bundle
- frontend: not required
- observability: execute canonical `today-week` post-test review

## Execution Hints
- workdir: /opt/astro-project
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- touches_frontend: False
- requires_frontend_visual: False

## Reviewer Gate
- Verifier must report exact commands, PASS or FAIL result, and final observability verdict.
- Green tests alone are insufficient without the canonical post-test evidence review.

## Dependencies
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-ARCHITECT-WAVE-GATE

## Notes
- This is the only wave that owns canonical `today-week` closeout for this feature.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Verifier Evidence",
  "summary": "Run the final canonical backend and today-week observability lanes for the completed backend active slice and record the explicit closeout verdict.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-ARCHITECT-WAVE-GATE",
    "/opt/astro-project/docs/backend-grace-observability-wave-tz/verification-matrix.slice.backend-grace-observability-wave-tz.md"
  ],
  "acceptance_criteria": [
    "backend:quick command passes or failure is attached with exact failing test and traceback summary.",
    "Targeted backend active-slice pytest command passes or failure is attached with exact failing test and traceback summary.",
    "Final today-week post-test review completes and yields an explicit clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker verdict.",
    "If observability evidence is absent, fragmented, or unexpectedly degraded, verifier blocks acceptance."
  ],
  "verification_profile": {
    "backend": "execute backend:quick and the targeted backend active-slice pytest bundle",
    "frontend": "not required",
    "observability": "execute canonical today-week post-test review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "runner": "codex",
    "backend_commands": [
      "docker exec astro-project-backend-1 python3 scripts/pipeline.py",
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py"
    ],
    "observability_commands": [
      "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false
  },
  "reviewer_gate": [
    "Verifier must report exact commands, PASS or FAIL result, and final observability verdict.",
    "Green tests alone are insufficient without the canonical post-test evidence review."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-ARCHITECT-WAVE-GATE"
  ],
  "notes": [
    "This is the only wave that owns canonical today-week closeout for this feature."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
