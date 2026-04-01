# GRACE HOME

`docs/GRACE_HOME.md` is the project-local home for how strict GRACE is applied inside `/opt/astro-project`.

## Source order

1. `AGENTS.md` — repo operating rules, agent roles, and required verification protocol
2. `GRACE.md` — strict GRACE baseline and hard requirements
3. Slice-specific packets and maps under `docs/` — local execution artifacts for active bounded work

If there is a conflict, the stronger source wins in that order unless `GRACE.md` explicitly says otherwise.

## Durable project interpretation

- Work is artifact-first, not code-first.
- Agents operate inside bounded slices with explicit verification.
- Minimal sufficient regression is preferred over blind full reruns.
- Durable global docs should stay short and role-clear.
- Packet-specific details should stay near the packet, not be recopied into global indices.

## Core homes

- `docs/TESTING.md` — how agents choose and run verification
- `docs/FIXTURES.md` — canonical regression fixtures and manifest
- `docs/REGRESSION_MAP.md` — master durable regression map

## Supporting references

- `docs/GRACE_ARTIFACTS.md` — legacy artifact inventory still used by some tooling and historical workflows
- `docs/WORKFLOW.md` — adjacent workflow/operations guidance
- `automation/README.md` — background-task and evidence automation details

## Wave 1 consolidation rule

For wave 1, new global truth is intentionally minimal. Migrate only durable cross-slice guidance here. Keep audits, packets, benchmark notes, and rollout-specific maps in their existing local docs with short pointers back to these homes when needed.
