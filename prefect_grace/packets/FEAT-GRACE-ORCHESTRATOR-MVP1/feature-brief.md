# Feature Brief: GRACE Orchestrator MVP-1 Project Adapter And Packet Contracts

## Feature ID

`FEAT-GRACE-ORCHESTRATOR-MVP1`

## Business Goal

Make the current `prefect_grace` prototype safe enough to consume GRACE
controller packets as formal source-of-truth artifacts before launching
agents. This is the first step toward the portable GRACE orchestration
platform described in:

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`

The goal is not to replace Prefect and not to execute agents yet. The goal is
to create a deterministic project adapter, packet parser, packet registry
contract, verification profile contract, and scope guard primitives that can
be tested locally inside `/opt/astro-project`.

## Why This Exists

The current implementation can run Prefect flows and Codex agents, but the
GRACE safety boundary is still too implicit:

- packets are treated mostly as operational files, not validated contracts;
- runtime state and source packets are not clearly separated;
- allowed/frozen scope is not enforced before agent launch;
- verifier profiles are not a stable project-level interface;
- CLI output is not consistently machine-readable;
- Prefect still leaks into domain semantics more than it should.

This packet creates the non-agent foundation so later waves can wire Prefect,
Codex, reviewer, rework, and merge logic onto explicit contracts.

## Non-Goals

- Do not launch Codex.
- Do not change agent prompts.
- Do not change existing Prefect deployments.
- Do not implement Temporal/GitHub Actions/local runner adapters.
- Do not move runtime state to Postgres.
- Do not refactor product backend/frontend.
- Do not touch `/opt/solarsage-astro`.

## Expected Outcome

After this feature:

1. The project has a versioned `prefect_grace/project.yaml` adapter.
2. Verification profiles are declared as data, not hardcoded ad hoc command
   lists.
3. New controller packets can be parsed into a typed model.
4. Existing legacy packets are warning-only, not blocking.
5. New strict packets can be validated and rejected before agent execution.
6. Scope guard functions can decide whether changed paths are inside allowed
   write scope.
7. CLI commands have `--json` output suitable for Prefect artifacts and
   future operator dashboards.

