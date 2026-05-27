# Feature Brief: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN

## Business Intent
Rerun backend active-slice strict-GRACE canon sync after fixing evidence ownership, rework sandbox propagation, and GRACE refs.

## Desired Outcome
Backend Active Slice GRACE Canon Sync Rerun

## In Scope
- Add and align GRACE module contracts, module maps, function contracts, and START/END semantic blocks for backend active-slice entrypoints.
- Cover main.py, logging_utils.py, day_brief.py, week_brief_service.py, scheduler.py, analytics.py, day_brief_validators.py, and correlation/logging glue.
- Preserve business semantics and use existing well-marked modules as local style references.

## Out of Scope
- Do not change scoring logic.
- Do not change Day or Week business semantics.
- Do not perform maximal logging rewrite.
- Do not deeply split report_workflow.py.
- Do not change frontend/UI.

## Impacted Surfaces
- backend
- observability

## Impacted GRACE Artifacts
- requirements.xml
- technology.xml
- development-plan.xml
- knowledge-graph.xml
- verification-matrix.md

## Acceptance Criteria
- Backend active slice is formally addressable by module/function/block.
- Packet-local gates use packet-local evidence only.
- Final verifier lane owns any canonical runtime observability gate.
- docker exec astro-project-backend-1 python3 scripts/pipeline.py remains green.

## Visual Expectations
-

## Wave Proposal
1. W00 architect + planner canon sync using current strict evidence taxonomy
2. W01 backend canon sync implementation
3. W02 final verification + review + architect gate

## Open Decisions
- Reuse current backend active-slice boundaries unless the architect finds a concrete scope conflict.
- Treat packet-local evidence and wave-final canonical evidence as separate lanes.
- Do not attach today-week canonical observability to packet-local implementation packets.
