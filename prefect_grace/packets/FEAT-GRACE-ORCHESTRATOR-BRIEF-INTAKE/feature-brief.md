# Feature Brief: FEAT-GRACE-ORCHESTRATOR-BRIEF-INTAKE

## Business Intent
Teach the Architect and Planner roles to automatically generate strict execution packets directly from a business brief. This eliminates manual editing, accelerates the W00 phase, and ensures that all safety boundaries and validation gates are programmatically checked and populated from day one.

## Desired Outcome
An automated intake system that reads a feature brief markdown file, parses its structured and unstructured sections, and generates a fully compliant, strict `EXECUTION_PACKET.md` and sidecar `EXECUTION_PACKET.yaml` that passes the strict packet validation checks without warnings.

## In Scope
- Automatic parsing of feature brief sections (Business Intent, Scope, Impacted Surfaces, etc.).
- Generation of the structured `EXECUTION_PACKET.md` with strict formatting.
- Generation of the `EXECUTION_PACKET.yaml` sidecar representing canonical parsed fields.
- Integration into the GRACE W00 phase (Architect / Planner workflows).
- Integration test suite validating correct generation and validation status.

## Out of Scope
- Mutating actual production code outside of the intake platform modules and tests.
- Broad changes to unrelated packages.

## Impacted Surfaces
- backend: W00 planning logic and pipeline.
- automation: intake scripting and generation CLI entrypoints.

## Impacted GRACE Artifacts
- development-plan.xml: slice definitions.
- requirements.xml: automated planning contract constraints.

## Acceptance Criteria
- Auto-generated packets must pass strict validation: `validate-packet --strict`.
- Sidecar YAML must match markdown packet ID, feature ID, and write/frozen scopes.
- Generated packet contains clear write scope, frozen scope, and expected evidence sections.

## Visual Expectations
- None (CLI and backend automation only).

## Wave Proposal
1. Implement the Brief Intake Orchestrator MVP that automatically generates packets.
2. Verify correctness using targeted CLI and platform contract tests.

## Open Decisions
- Should the intake CLI command support direct overrides for allowed/frozen scopes?
