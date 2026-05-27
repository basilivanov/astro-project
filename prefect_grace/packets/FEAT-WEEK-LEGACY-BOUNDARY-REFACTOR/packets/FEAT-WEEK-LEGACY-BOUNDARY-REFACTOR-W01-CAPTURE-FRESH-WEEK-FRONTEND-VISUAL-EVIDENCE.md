# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Title
Capture Fresh Week Frontend Visual Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Packet Type
rework

## Summary
Produce fresh frontend visual proof for the Week legacy boundary refactor without changing product code. The rework must satisfy the existing requires_frontend_visual=true contract by capturing current /week canonical and fail-closed states after the implemented helper split.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR`

## Write Scope
- /opt/astro-project/test-results/rendered-gate/**/*
- /opt/astro-project/frontend/test-results/**/*
- /opt/astro-project/frontend/playwright-report/**/*
- /opt/astro-project/test-results/**/*
- /opt/astro-project/.task-logs/**/*

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-VERDICT
- Latest verifier evidence showing executable tests passed and packet-local observability is degraded-but-expected

## Acceptance Criteria
- Fresh frontend visual evidence is attached for the canonical /week state covered by e2e/canonical-week-continuity.spec.ts.
- Fresh frontend visual evidence is attached for the legacy-only fail-closed /week state covered by e2e/week-page-fallback.spec.ts.
- No production source files are changed unless the visual run exposes a real regression; if that happens, stop and route back with the exact regression instead of widening this rework.
- The rework notes list exact commands run, artifact paths produced, and PASS/FAIL result.
- The final verifier/reviewer handoff explicitly states whether visual proof satisfies requires_frontend_visual=true.

## Verification Profile
- backend: not required
- frontend: ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts with screenshots/traces retained as fresh visual evidence
- observability: packet_local remains valid; no today-week canonical closeout is required. Preserve degraded-but-expected if no canonical runtime emitter is intentionally owned here.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to narrow packet-local write scope

## Reviewer Gate
- Accept only if fresh visual artifacts exist and are referenced by path.
- Accept only if the visual evidence covers both canonical Week continuity and legacy-only fail-closed behavior.
- Reject if production source changes occur without a concrete visual regression explanation.
- Do not require a today-week canonical gate for this evidence-only rework.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR

## Notes
- This is evidence completion, not feature reslicing.
- Planner is not required.
- The existing packet-local observability verdict is not a blocker when explicitly recorded as degraded-but-expected.
- Keep the rework bounded to visual artifacts and reviewer/verifier handoff notes.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Capture Fresh Week Frontend Visual Evidence",
  "summary": "Produce fresh frontend visual proof for the Week legacy boundary refactor without changing product code. The rework must satisfy the existing requires_frontend_visual=true contract by capturing current /week canonical and fail-closed states after the implemented helper split.",
  "write_scope": [
    "/opt/astro-project/test-results/rendered-gate/**/*",
    "/opt/astro-project/frontend/test-results/**/*",
    "/opt/astro-project/frontend/playwright-report/**/*",
    "/opt/astro-project/test-results/**/*",
    "/opt/astro-project/.task-logs/**/*"
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-VERDICT",
    "Latest verifier evidence showing executable tests passed and packet-local observability is degraded-but-expected"
  ],
  "acceptance_criteria": [
    "Fresh frontend visual evidence is attached for the canonical /week state covered by e2e/canonical-week-continuity.spec.ts.",
    "Fresh frontend visual evidence is attached for the legacy-only fail-closed /week state covered by e2e/week-page-fallback.spec.ts.",
    "No production source files are changed unless the visual run exposes a real regression; if that happens, stop and route back with the exact regression instead of widening this rework.",
    "The rework notes list exact commands run, artifact paths produced, and PASS/FAIL result.",
    "The final verifier/reviewer handoff explicitly states whether visual proof satisfies requires_frontend_visual=true."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts with screenshots/traces retained as fresh visual evidence",
    "observability": "packet_local remains valid; no today-week canonical closeout is required. Preserve degraded-but-expected if no canonical runtime emitter is intentionally owned here."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to narrow packet-local write scope"
  },
  "reviewer_gate": [
    "Accept only if fresh visual artifacts exist and are referenced by path.",
    "Accept only if the visual evidence covers both canonical Week continuity and legacy-only fail-closed behavior.",
    "Reject if production source changes occur without a concrete visual regression explanation.",
    "Do not require a today-week canonical gate for this evidence-only rework."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR"
  ],
  "notes": [
    "This is evidence completion, not feature reslicing.",
    "Planner is not required.",
    "The existing packet-local observability verdict is not a blocker when explicitly recorded as degraded-but-expected.",
    "Keep the rework bounded to visual artifacts and reviewer/verifier handoff notes."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "light_resume",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
