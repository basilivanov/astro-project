# Feature Brief: FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ

## Business Intent
Подготовить текущий backend active slice к безопасному глубокому рефактору и стабильной multi-agent разработке: переиспользовать уже утвержденную strict-GRACE boundary и довести development-critical path до trace-first structured observability без изменения продуктовой бизнес-логики.

## Desired Outcome
Backend GRACE Canon Sync + Full Dev Observability

## In Scope
- Reuse the existing backend active-slice boundary already encoded in root GRACE canon: `M-API-GATEWAY`, `M-TRACE-LOGGING`, `M-DAY-BRIEF-SERVICE`, `M-WEEK-BRIEF-SERVICE`, `M-ANALYTICS-EVENTS`, `M-OPS-AUTOMATION`.
- Close remaining module-contract, module-map, function-contract, and semantic-block gaps on the bounded backend file set.
- Add dense development-phase structured observability on exported, orchestration, and side-effect boundaries in the same bounded backend file set.
- Keep packet-local read-only evidence separate from the final canonical `today-week` observability lane.
- Materialize architect slice docs and a direct-execution packet graph for this feature without forcing planner decomposition.

## Out of Scope
- Product-behavior, scoring, payload, auth, billing, referral, or frontend changes.
- Deep decomposition of `backend/app/services/report_workflow.py`.
- Repo-wide logging cleanup or a new logging transport or envelope.
- Frontend visual or Day or Week runtime-indicator work.
- Unbounded refactors outside the approved backend active slice.

## Impacted Surfaces
- backend: `backend/app/main.py`, `backend/app/logging_utils.py`, `backend/app/middleware/correlation.py`, `backend/app/services/day_brief.py`, `backend/app/services/day_brief_validators.py`, `backend/app/services/week_brief_service.py`, `backend/app/services/scheduler.py`, `backend/app/services/analytics.py`
- observability: packet-local read-only evidence in W01 and W02, canonical `today-week` closeout in W03
- grace: feature-local slice docs, wave topology, packet graph, and reviewer and verifier gates

## Impacted GRACE Artifacts
- requirements.xml: reuse the current backend active-slice canon; no new business invariant is expected unless code inspection exposes a gap.
- technology.xml: reuse the current bounded file-set and logging-envelope constraints; no tooling delta is expected.
- development-plan.xml: reuse the current backend active-slice canon and dev-observability sequencing; no new root packet family is expected.
- knowledge-graph.xml: reuse the current backend active-slice module and flow links; feature-local slice docs must carry this feature's packet graph detail.
- verification-matrix.md: reuse the existing backend active-slice packet-local and wave-final lanes; feature-local slice matrix must bind them to this feature's waves.

## Acceptance Criteria
- Feature-local slice docs and architect manifest exist before execution.
- W01 is limited to backend active-slice canon gap closure.
- W02 is limited to dense development-phase observability on the same bounded backend slice.
- W03 owns canonical `today-week` closeout and blocks on `unexpected-degradation` or `no-evidence-blocker`.
- No planner dependency remains on the critical path unless architect later reopens packet topology.
- No frontend or business-semantic drift is introduced.

## Visual Expectations
- None. This is a backend-only slice and does not own frontend visual proof.

## Wave Proposal
1. W00 architect formalization binds the feature to the existing backend active-slice canon and writes the slice-local packet graph.
2. W01 closes remaining backend active-slice contract, map, function-contract, and semantic-block gaps with packet-local evidence only.
3. W02 adds dense backend development-phase observability on the same bounded file set with packet-local evidence only.
4. W03 runs final canonical verification, reviewer closeout, and architect gate on the completed backend slice.

## Open Decisions
- No blocking architectural decision remains if the feature reuses the existing backend active-slice boundary already encoded in root GRACE.
- Planner stays optional and should remain skipped unless the wave or packet topology changes after implementation or review.
