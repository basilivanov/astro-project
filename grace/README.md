# GRACE Artifact Pack

This folder contains the strict-GRACE artifact pack required by `docs/GRACE_CANON.md` §13 (Definition of Ready).

## Source-of-truth order

1. `docs/GRACE_CANON.md` — methodology canon (portable, transferable).
2. `docs/10_GRACE_Project_Agent_Guide.md` — local adaptation for this project.
3. Artifacts in this folder — the binding plan.
4. `docs/00..13_*.md` — domain truth.
5. Code under `app/`, `apps/api/`, `apps/solarsage/`, `packages/contracts/`, etc.

If a code artifact contradicts a higher-priority artifact, the higher-priority one wins.

## Files

| File | GRACE clause | Purpose |
|---|---|---|
| `requirements.xml` | §13.A | Use cases, business rules, invariants, NFRs |
| `technology.xml` | §13.B | Stack, boundaries, version policy, local adaptations |
| `development-plan.xml` | §13.C | Phases, waves, write-scope, freeze-scope |
| `knowledge-graph.xml` | §13.D | Modules, dependencies, contracts, versions |
| `verification-matrix.md` | §13.E | UC ⇄ module gates ⇄ scenarios |

## Naming conventions (semantic coordinates §6)

- Use cases: `UC-*` (e.g. `UC-DAY-VIEW`)
- Modules: `M-*` (e.g. `M-DAY-SERVICE`)
- Phases: `PHASE-N-NAME` (e.g. `PHASE-1-MOCKED-PIPELINE`)
- Waves: `W-N.M` (e.g. `W-1.1`)
- Contracts: `C-*` (e.g. `C-TODAY-PAYLOAD`)
- Versions: `contract_version`, `calculation_version`, `normalization_version`, `scoring_version`, `prompt_version`, `content_version`, `schema_version`

## Pilot slice

`UC-DAY-VIEW` over `M-DAY-SERVICE` returning fixture-backed `TodayPayload`. See `development-plan.xml` → `PHASE-1-MOCKED-PIPELINE` → `W-1.3`.
