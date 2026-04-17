# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-EVIDENCE

## Title
Week Boundary Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-EVIDENCE`

## Packet Type
execution

## Summary
Produce fresh targeted Week unit, route, Playwright, visual, and packet-local read-only observability evidence for rerun-B.

## Wave
W01

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B/evidence/**
- /opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417-b/**

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W00-ARCHITECT-FORMALIZATION
- coder_main output
- execution packet
- architect manifest

## Acceptance Criteria
- All targeted commands are executed and recorded with PASS or FAIL status.
- Evidence covers canonical Week continuity and fail-closed legacy-only empty state.
- Visual proof includes fresh rerun-B canonical and fail-closed captures or attachments.
- Console and page-error hygiene is recorded for targeted Playwright flows.
- Read-only observability review is recorded as clean or degraded-but-expected; unexpected-degradation and no-evidence-blocker block acceptance.
- Evidence explicitly states that canonical Today/Week runtime closeout is not owned by this wave.

## Verification Profile
- backend: not required for this frontend-only wave; if backend drift is detected, block and route back because it is outside scope
- frontend: python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; observability_scope=packet_local; degraded-but-expected allowed

## Execution Hints
- workdir: /opt/astro-project
- runner: codex
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Reject if any required command is skipped without explicit blocker.
- Reject if visual proof does not show both canonical and fail-closed states.
- Reject if observability is missing, fragmented, unexpected-degradation, or no-evidence-blocker.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN

## Notes
- Fresh canonical Today or Week emitter evidence is not required here.
- If a page crash or 500 appears, block verification and require a reproduction test before rerunning.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Week Boundary Evidence",
  "summary": "Produce fresh targeted Week unit, route, Playwright, visual, and packet-local read-only observability evidence for rerun-B.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B/evidence/**",
    "/opt/astro-project/frontend/docs/review_evidence/front/week-boundary-rerun-20260417-b/**"
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W00-ARCHITECT-FORMALIZATION",
    "coder_main output",
    "execution packet",
    "architect manifest"
  ],
  "acceptance_criteria": [
    "All targeted commands are executed and recorded with PASS or FAIL status.",
    "Evidence covers canonical Week continuity and fail-closed legacy-only empty state.",
    "Visual proof includes fresh rerun-B canonical and fail-closed captures or attachments.",
    "Console and page-error hygiene is recorded for targeted Playwright flows.",
    "Read-only observability review is recorded as clean or degraded-but-expected; unexpected-degradation and no-evidence-blocker block acceptance.",
    "Evidence explicitly states that canonical Today/Week runtime closeout is not owned by this wave."
  ],
  "verification_profile": {
    "backend": "not required for this frontend-only wave; if backend drift is detected, block and route back because it is outside scope",
    "frontend": "python3 -m pytest -q tests/test_week_brief_frontend_mapping.py; corepack pnpm --dir frontend exec jest --runInBand test/app/week-page.test.tsx test/lib/week-brief.test.ts; ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; observability_scope=packet_local; degraded-but-expected allowed"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Reject if any required command is skipped without explicit blocker.",
    "Reject if visual proof does not show both canonical and fail-closed states.",
    "Reject if observability is missing, fragmented, unexpected-degradation, or no-evidence-blocker."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN"
  ],
  "notes": [
    "Fresh canonical Today or Week emitter evidence is not required here.",
    "If a page crash or 500 appears, block verification and require a reproduction test before rerunning."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
