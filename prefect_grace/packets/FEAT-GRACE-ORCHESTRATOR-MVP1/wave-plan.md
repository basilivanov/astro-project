# Wave Plan: GRACE Orchestrator MVP-1

## Feature ID

`FEAT-GRACE-ORCHESTRATOR-MVP1`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/feature-brief.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP1/EXECUTION_PACKET.md`

## Wave W01 — Project Adapter And Contract Parser

### Role

Coder.

### Reasoning

High.

### Goal

Create the reusable, testable GRACE contract layer inside `prefect_grace`
without executing agents or changing Prefect runtime behavior.

### Packets

- `FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS`

### Deliverables

- Project adapter loader.
- Verification profile loader.
- Controller packet parser.
- Source hash normalization excluding runtime sections.
- Scope guard primitives.
- YAML-backed runtime store interfaces or stubs with tests.
- CLI commands with `--json`.
- Unit tests proving valid/invalid behavior.

### Gate

The wave is accepted only if tests prove:

- a valid project adapter loads;
- a valid strict packet parses;
- an invalid strict packet is rejected;
- legacy packets can be scanned in warning mode;
- source hash ignores `## Evidence` and `## Reviewer notes`;
- changed paths outside allowed scope are rejected;
- CLI JSON output is stable and machine-readable.

