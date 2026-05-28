# Execution Packet: FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER-W01-SCOPED-APPLY

## Objective
Add fail-closed packet id filtering to `registry-bootstrap-apply` so operators can dry-run or apply exactly selected bootstrap packet candidates without mutating other planned registry candidates.

## Slice
- slice_id: `SLICE-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER`
- slice_slug: `grace-registry-bootstrap-apply-packet-filter`
- feature_id: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER`
- packet_id: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER-W01-SCOPED-APPLY`
- wave_id: `W01`
- status: `ready_for_review`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-W01-SOURCE-TO-RUNTIME`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER`

## Source Of Truth
- `/opt/astro-project/prefect_grace/platform/registry_bootstrap_apply.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/cli_commands/project_registry.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_registry_bootstrap_apply.py`
- `/opt/astro-project/tests/test_prefect_grace_controller_backlog_bootstrap.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

## Impacted Modules
- `M-GRACE-REGISTRY-BOOTSTRAP-APPLY`
- `M-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Required Design Decisions
1. `--packet-id` is optional and repeatable; no filter preserves whole-project behavior.
2. Packet ids are normalized by trimming whitespace, removing duplicates, and sorting deterministically.
3. Blank packet ids fail closed with `PACKET_FILTER_INVALID`.
4. Requested ids absent from source packet candidates fail closed with `PACKET_FILTER_NOT_FOUND`.
5. Filtering is applied before registry writes, so apply mode cannot upsert unselected candidates.
6. JSON output includes both `packet_ids` and `packet_filter`.
7. No live agents, Docker, backend, frontend, or real runtime registry apply are allowed for this packet.

## Allowed Write Scope
- prefect_grace/platform/registry_bootstrap_apply.py
- prefect_grace/platform/controller_backlog_bootstrap.py
- prefect_grace/cli_commands/project_registry.py
- prefect_grace/cli_commands/parser.py
- tests/test_prefect_grace_registry_bootstrap_apply.py
- tests/test_prefect_grace_controller_backlog_bootstrap.py
- tests/test_prefect_grace_cli_contracts.py
- prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**
- prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**
- /var/lib/grace-orchestrator/**

## Must Preserve
- Existing unfiltered `registry-bootstrap-apply` dry-run and apply behavior.
- Existing CLI JSON envelope shape where `result == data`.
- Source packet files and source evidence are read-only inputs during runtime bootstrap apply.
- Runtime registry writes remain bounded under the configured `runtime_state_root`.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_registry_bootstrap_apply.py tests/test_prefect_grace_controller_backlog_bootstrap.py tests/test_prefect_grace_cli_contracts.py`
- `python3 -m compileall -q prefect_grace/platform/registry_bootstrap_apply.py prefect_grace/platform/controller_backlog_bootstrap.py prefect_grace/cli_commands/project_registry.py prefect_grace/cli_commands/parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/registry_bootstrap_apply.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/controller_backlog_bootstrap.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/project_registry.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER/EVIDENCE/attempt-0001 --json`
- `git diff --check`

## Expected Evidence
- `EVIDENCE/attempt-0001/evidence_manifest.json`
- `EVIDENCE/attempt-0001/SUMMARY.md`
- Verification command outputs recorded in the bounded summary artifact.

## Escalation Triggers
- Any selected apply mutates an unselected registry packet.
- Missing requested packet ids do not fail closed.
- Blank packet ids are silently accepted.
- Existing unfiltered behavior regresses.
- CLI JSON envelope no longer keeps `result == data`.
