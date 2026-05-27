# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-E2E-GUARDRAIL-UPDATES

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-E2E-GUARDRAIL-UPDATES`

## Summary
Update only the allowed Week E2E guardrail specs if required to reflect the backend boundary and frontend helper split while proving fallback safety and canonical continuity remain unchanged.

## Wave
W01

## Role
coder

## Reasoning
medium

## Write Scope
- /opt/astro-project/frontend/e2e/week-page-fallback.spec.ts
- /opt/astro-project/frontend/e2e/canonical-week-continuity.spec.ts

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT
- /opt/astro-project/docs/week-legacy-boundary-refactor/verification-matrix.slice.week-legacy-boundary-refactor.md

## Acceptance Criteria
- Week fallback safety and canonical continuity E2E specs remain aligned with unchanged visible Week behavior.
- No visible Week product states are added or changed; required visible states remain canonical, empty, in_progress, and error.
- E2E updates, if any, are limited to allowed guardrail specs and do not encode new product semantics.
- If no E2E spec edits are needed, packet records that existing specs already cover the required VM-WEEK-LEGACY-BOUNDARY-E2E behavior.

## Verification Profile
- backend: Backend health is exercised by the Playwright wrapper, but this packet does not own backend implementation verification.
- frontend: Run the targeted Week Playwright guardrails through the Playwright container. Visual evidence is required only if these specs or changes produce screenshots/rendered artifacts; no visible UI file changes are allowed.
- observability: Coder should record local Playwright artifacts only; packet-local post-test review is owned by the verifier packet.
- execution:
  - backend_commands:
  - frontend_commands:
    - ./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/canonical-week-continuity.spec.ts
  - observability_scope: none
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

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- E2E guardrails prove existing Week fallback safety and canonical continuity without changing visible Week semantics.
- No forbidden visible UI files are changed.
- Playwright ran through ./scripts/run_e2e.sh, not frontend_dev browser execution.
- Any screenshot or rendered-gate artifact produced by the E2E lane is listed for verifier/reviewer inspection.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## Notes
- This packet should be small; do not add broad E2E cleanup or unrelated route coverage.
- The architect slice says separate frontend visual proof is not required unless implementation leaks into visible Week UI files, but this packet makes visual artifact expectations explicit because it touches frontend E2E guardrails.
