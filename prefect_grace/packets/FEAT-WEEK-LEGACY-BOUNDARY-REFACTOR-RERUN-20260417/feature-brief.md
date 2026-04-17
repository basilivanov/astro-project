# Feature Brief: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417

## Business Intent
Повторно пройти week legacy boundary scope как новую business feature line: сохранить canonical Week continuity, fail-closed empty-state поведение и frontend week compatibility boundary без product regression.

## Desired Outcome
Canonical `/week` remains canonical-only, legacy-only Week payloads fail closed to honest empty/create UI, and compatibility reconstruction stays explicit and isolated from the product route.

## In Scope
- Formalize the feature into GRACE artifacts.
- Slice the feature into bounded execution packets.
- Prepare implementation, verification, and review flow.

## Out of Scope
- Full production rollout of the feature.
- Unbounded refactors outside the packet scopes.

## Impacted Surfaces
- frontend: `/week` route boundary, Week brief adapters, and Week-specific tests/visual evidence only.
- automation: feature-local packet orchestration artifacts only; no pipeline contract change is owned here.
- observability: packet-local read-only evidence only; no canonical Week emitter closeout is owned by this slice.

## Impacted GRACE Artifacts
- requirements.xml: only if the business scope/invariants change.
- technology.xml: only if the runtime/tooling contract changes.
- development-plan.xml: only if execution topology or packet model changes.
- knowledge-graph.xml: only if module/slice links change.
- verification-matrix.md: only if verification gates or evidence rules change.

## Acceptance Criteria
- Canonical `/week` uses only `week_brief` or `week_brief_envelope.data` to build the product surface.
- Legacy-only `week_map`, chunks, or raw legacy fields do not synthesize a substitute `/week` product surface.
- Missing canonical Week payload renders honest empty/create UI without leaking raw internal tokens.
- Targeted frontend verification and packet-local observability evidence are sufficient to review and gate the wave.

## Visual Expectations
- Canonical Week surface preserves current primary CTA and completed-content hierarchy when canonical `week_brief` exists.
- Legacy-only or missing canonical Week state renders the empty/create surface, not a compatibility substitute.
- In-progress Week state stays top-layer only and does not expose completed deep content prematurely.
- User-visible Week UI does not leak raw internal legacy/fallback/debug tokens.

## Wave Proposal
1. W00 architect formalization aligns feature-local artifacts, packet graph, and bounded Week scope.
2. W01 executes the single bounded frontend Week boundary packet, verifier evidence, reviewer verdict, and architect wave gate.
3. Planner stays off by default and is introduced only if this frontend-only decomposition can no longer remain bounded.

## Open Decisions
- No open business decision at formalization time.
- Escalate only if the Week boundary rerun proves to require backend/schema changes or more than one implementation packet.
