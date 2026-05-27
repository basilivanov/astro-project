# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FIX-WEEK-CANONICAL-NAVIGATION-AND-FAIL-CLOSED-EMPTY-STATE

## Title
Fix Week Canonical Navigation and Fail-Closed Empty State

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FIX-WEEK-CANONICAL-NAVIGATION-AND-FAIL-CLOSED-EMPTY-STATE`

## Packet Type
rework

## Summary
Fix the Week frontend regressions proven by fresh visual evidence: canonical Week continuity must navigate from /week to the canonical /read/... route, and legacy-only inputs must render the expected fail-closed empty Week state. After the fix, rerun the targeted visual verifier with fresh artifacts.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Write Scope
- /opt/astro-project/frontend/app/week/page.tsx
- /opt/astro-project/frontend/components/week/**
- /opt/astro-project/frontend/lib/week-brief.ts
- /opt/astro-project/frontend/lib/week-brief-compat.ts
- /opt/astro-project/frontend/test/lib/week-brief.test.ts
- /opt/astro-project/tests/test_week_brief_frontend_mapping.py
- /opt/astro-project/frontend/e2e/week-page-fallback.spec.ts
- /opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts
- /opt/astro-project/frontend/test-results/**/*
- /opt/astro-project/frontend/playwright-report/**/*
- /opt/astro-project/test-results/**/*
- /opt/astro-project/.task-logs/**/*

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE
- Fresh failure evidence under /opt/astro-project/frontend/test-results/verifier-week-visual-20260416-01

## Acceptance Criteria
- Canonical Week continuity no longer stays on /week?mock=1 after the primary CTA; it navigates to the expected /read/... route.
- Legacy-only Week inputs render the fail-closed empty state with the copy `Персональной недели пока нет`.
- The canonical /week product path remains canonical-only and does not reconstruct legacy week_map/chunks as a substitute Week surface.
- The Week compatibility helper remains isolated from the canonical mapper.
- No backend files or broad unrelated frontend files are changed.
- Fresh visual artifacts are produced for both canonical continuity and legacy-only fail-closed behavior.

## Verification Profile
- backend: not required unless the coder unexpectedly touches backend files; if touched, run docker exec astro-project-backend-1 python3 scripts/pipeline.py and explain why backend scope changed
- frontend: Run python3 -m pytest -q tests/test_week_brief_frontend_mapping.py, corepack pnpm --dir frontend exec jest --runInBand test/lib/week-brief.test.ts, and ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts with screenshots/traces retained
- observability: packet_local remains the contract. Run python3 tools/post_test_review.py --profile read-only --since 30m --report-format md after the targeted E2E run; degraded-but-expected is acceptable only if no canonical runtime emitter was intentionally owned by this rework.

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to narrow packet-local write scope

## Reviewer Gate
- Reject if the fix only relaxes assertions while preserving the visual regressions.
- Reject if legacy reconstruction re-enters the canonical /week product path.
- Reject if the primary CTA still keeps the user on /week?mock=1 in canonical continuity.
- Reject if the legacy-only path does not show the expected empty-state copy.
- Accept only with fresh screenshot or trace paths for both repaired visual states.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Notes
- This packet intentionally unlocks minimal visible Week route/component scope because the evidence-only rework proved a user-visible regression.
- Do not reslice the feature and do not request planner involvement.
- Do not add a today-week canonical closeout; this remains packet-local evidence.
- If the fix requires changing backend payload semantics, stop and route back to architect instead of widening scope.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FIX-WEEK-CANONICAL-NAVIGATION-AND-FAIL-CLOSED-EMPTY-STATE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Fix Week Canonical Navigation and Fail-Closed Empty State",
  "summary": "Fix the Week frontend regressions proven by fresh visual evidence: canonical Week continuity must navigate from /week to the canonical /read/... route, and legacy-only inputs must render the expected fail-closed empty Week state. After the fix, rerun the targeted visual verifier with fresh artifacts.",
  "write_scope": [
    "/opt/astro-project/frontend/app/week/page.tsx",
    "/opt/astro-project/frontend/components/week/**",
    "/opt/astro-project/frontend/lib/week-brief.ts",
    "/opt/astro-project/frontend/lib/week-brief-compat.ts",
    "/opt/astro-project/frontend/test/lib/week-brief.test.ts",
    "/opt/astro-project/tests/test_week_brief_frontend_mapping.py",
    "/opt/astro-project/frontend/e2e/week-page-fallback.spec.ts",
    "/opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts",
    "/opt/astro-project/frontend/test-results/**/*",
    "/opt/astro-project/frontend/playwright-report/**/*",
    "/opt/astro-project/test-results/**/*",
    "/opt/astro-project/.task-logs/**/*"
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
    "Fresh failure evidence under /opt/astro-project/frontend/test-results/verifier-week-visual-20260416-01"
  ],
  "acceptance_criteria": [
    "Canonical Week continuity no longer stays on /week?mock=1 after the primary CTA; it navigates to the expected /read/... route.",
    "Legacy-only Week inputs render the fail-closed empty state with the copy `Персональной недели пока нет`.",
    "The canonical /week product path remains canonical-only and does not reconstruct legacy week_map/chunks as a substitute Week surface.",
    "The Week compatibility helper remains isolated from the canonical mapper.",
    "No backend files or broad unrelated frontend files are changed.",
    "Fresh visual artifacts are produced for both canonical continuity and legacy-only fail-closed behavior."
  ],
  "verification_profile": {
    "backend": "not required unless the coder unexpectedly touches backend files; if touched, run docker exec astro-project-backend-1 python3 scripts/pipeline.py and explain why backend scope changed",
    "frontend": "Run python3 -m pytest -q tests/test_week_brief_frontend_mapping.py, corepack pnpm --dir frontend exec jest --runInBand test/lib/week-brief.test.ts, and ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts with screenshots/traces retained",
    "observability": "packet_local remains the contract. Run python3 tools/post_test_review.py --profile read-only --since 30m --report-format md after the targeted E2E run; degraded-but-expected is acceptable only if no canonical runtime emitter was intentionally owned by this rework."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to narrow packet-local write scope"
  },
  "reviewer_gate": [
    "Reject if the fix only relaxes assertions while preserving the visual regressions.",
    "Reject if legacy reconstruction re-enters the canonical /week product path.",
    "Reject if the primary CTA still keeps the user on /week?mock=1 in canonical continuity.",
    "Reject if the legacy-only path does not show the expected empty-state copy.",
    "Accept only with fresh screenshot or trace paths for both repaired visual states."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE"
  ],
  "notes": [
    "This packet intentionally unlocks minimal visible Week route/component scope because the evidence-only rework proved a user-visible regression.",
    "Do not reslice the feature and do not request planner involvement.",
    "Do not add a today-week canonical closeout; this remains packet-local evidence.",
    "If the fix requires changing backend payload semantics, stop and route back to architect instead of widening scope."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
