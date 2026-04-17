# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD

## Title
Verifier Rework Fix Week Legacy Raw-Slug Fallback Guard

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: not required for this frontend-only wave; if backend drift is detected, block and route back because it is outside scope
- frontend: python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; observability_scope=packet_local; degraded-but-expected allowed

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to at most two small blocker reasons
- runner: codex
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Fix Week Legacy Raw-Slug Fallback Guard",
  "summary": "Validate the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "not required for this frontend-only wave; if backend drift is detected, block and route back because it is outside scope",
    "frontend": "python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; observability_scope=packet_local; degraded-but-expected allowed"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to at most two small blocker reasons",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
