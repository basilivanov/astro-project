# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC-RERUN-2

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC-RERUN-2`

## Summary
Formalize backend active-slice ownership boundaries, contracts, and semantic phases before deep refactor and logging-heavy follow-up waves. Scope: Add and align GRACE module contracts, module maps, function contracts, and START/END semantic blocks for backend active-slice entrypoints.; Cover main.py, logging_utils.py, day_brief.py, week_brief_service.py, scheduler.py, analytics.py, day_brief_validators.py, and correlation/logging glue.; Preserve business semantics and use existing well-marked modules as local style references.. Acceptance: Backend active slice is formally addressable by module/function/block.; Packet-local gates use packet-local evidence only.; Final verifier lane owns canonical backend runtime observability gate.; docker exec astro-project-backend-1 python3 scripts/pipeline.py remains green.. Non-goals: Do not change scoring logic.; Do not change Day or Week business semantics.; Do not perform maximal logging rewrite.; Do not deeply split report_workflow.py.; Do not change frontend/UI..

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2-W00-ARCHITECT-FORMALIZATION
- feature brief

## Acceptance Criteria
- Requested code change is implemented within scope.
- Targeted tests are added or updated if needed.
- Implementation notes are left for verifier and reviewer.

## Verification Profile
- backend: backend:quick or targeted tests as required by the packet
- frontend: targeted Playwright run if the packet touches UI
- observability: post-test log, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-2-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
