# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-WAVE-VERDICT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-WAVE-VERDICT`

## Summary
Perform final technical review of all W01 coder packets and verifier evidence against the architect slice contract, frozen scope, and acceptance criteria.

## Wave
W01

## Role
reviewer

## Reasoning
high

## Write Scope
-

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FRONTEND-WEEK-COMPATIBILITY-SPLIT
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-E2E-GUARDRAIL-UPDATES
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-WEEK-E2E-GUARDRAILS
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-PACKET-LOCAL-WEEK-BOUNDARY-EVIDENCE

## Acceptance Criteria
- Reviewer accepts the W01 wave or rejects it with concrete packet-keyed rework instructions.
- All coder packet write scopes stayed inside architect allowed_write_scope.
- Frozen scope remained untouched unless a prior architect escalation explicitly approved otherwise.
- All verifier commands required by the architect verification lane have PASS results or a documented blocker.
- Packet-local observability verdict is clean or degraded-but-expected.
- Reviewer confirms no canonical today-week wave-final gate was required or run for this packet-local architect wave.

## Verification Profile
- backend: Review backend diff and verifier evidence for Week seed ownership, prompt-context stability, fallback stability, and no forbidden backend rewrites.
- frontend: Review frontend diff and verifier evidence for canonical-only mapping, compatibility isolation, E2E guardrails, and unchanged visible Week UI.
- observability: Review packet-local read-only evidence and explicit verdict; today-week evidence is out of scope for this architect wave.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - test-results/rendered-gate/**/*
    - frontend/test-results/**/*
    - frontend/playwright-report/**/*
    - test-results/screens/**/*
    - frontend/test-results/screens/**/*
    - test-results/**/*
    - .task-logs/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only if backend seed ownership moved to week_brief_seed.py and week_brief_service.py no longer imports Week seed helpers from report_workflow.py private functions.
- Accept only if frontend/lib/week-brief.ts remains canonical-only and frontend/lib/week-brief-compat.ts owns compatibility reconstruction.
- Accept only if /week visible product behavior is unchanged and no visible Week UI files changed.
- Accept only if verifier evidence includes backend quick, targeted backend tests, frontend mapping tests, Jest helper tests, targeted Playwright E2E, and read-only packet-local post-test review.
- Reject if verifier verdict is unexpected-degradation or no-evidence-blocker.
- Reject if any out-of-scope file or frozen module changed without architect approval.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-WEEK-E2E-GUARDRAILS
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-PACKET-LOCAL-WEEK-BOUNDARY-EVIDENCE

## Notes
- This reviewer packet is the final technical acceptance gate before architect wave acceptance.
- If rejected, rework instructions must name the packet key that owns the fix.
