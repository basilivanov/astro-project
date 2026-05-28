# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN-W01-SOURCE-HASH-IMPACT

## Objective
Add a read-only migration impact planner that scans strict `EXECUTION_PACKET.md` packets, reports which canonical `EXECUTION_PACKET.yaml` sidecars would be created or updated, and shows source hash impact and runtime registry status without writing files.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN-W01-SOURCE-HASH-IMPACT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT-W01-CORPUS-DRY-RUN-REPORT`

## Impacted Modules
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-CLI`
- `M-GRACE-PACKET-VALIDATION`
- `M-GRACE-RUNTIME-REGISTRY`

## Allowed Write Scope
- prefect_grace/platform/packet_parser.py
- prefect_grace/platform/packet_yaml_sidecar_migration_plan.py
- prefect_grace/platform/packet_yaml_sidecar_audit.py
- prefect_grace/platform/packet_yaml_sidecar_sync.py
- prefect_grace/cli_commands/evidence.py
- prefect_grace/cli_commands/parser.py
- tests/test_prefect_grace_packet_yaml_sidecar_migration_plan.py
- tests/test_prefect_grace_cli_contracts.py
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- /var/lib/grace-orchestrator/**
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-WEEK-*/**

## Must Preserve
- Planner is read-only and must not create, update, or delete sidecars.
- Planner output always reports `writes: []`, `source_mutations: []`, `prefect_runs_created: 0`, and `live_agents_started: 0`.
- Discovery only includes files named exactly `EXECUTION_PACKET.md` below the packet root.
- Canonical packets are counted but are not included in plan items by default.
- Invalid sidecars and skipped packets are bounded findings and do not fail the command when the root scan completes.
- Missing or unreadable packet roots fail closed with `ok=false`.
- Missing or unloadable project config does not fail the plan; registry status is null and a warning is emitted.
- Runtime registry state, executor history, Prefect runs, live agents, backend, frontend, Docker, and Playwright remain untouched.

## Required Behavior
- Add `python3 -m prefect_grace.cli plan-packet-yaml-sidecar-migration [--packet-root prefect_grace/packets] [--project prefect_grace/project.yaml] [--json] [--limit N]`.
- Default packet root is `prefect_grace/packets`; default project config is `prefect_grace/project.yaml`.
- For strict packets classified as `no_sidecar` or `stale_sidecar`, emit plan items with `packet_id`, `packet_path`, `sidecar_path`, `planned_action`, `registry_status`, `current_source_hash`, `planned_source_hash`, `source_hash_changes`, and `risk`.
- Report counts by audit class, full plan count, risk counts, bounded items, bounded findings, and truncation signals.
- Cap `--limit` at 100 and default it to 20.
- Report `accepted_source_hash_change` when an accepted registry packet would change source hash.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_yaml_sidecar_migration_plan.py tests/test_prefect_grace_cli_contracts.py -q`
- `python3 -m compileall -q prefect_grace/platform/packet_parser.py prefect_grace/platform/packet_yaml_sidecar_migration_plan.py prefect_grace/cli_commands/evidence.py prefect_grace/cli_commands/parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_yaml_sidecar_migration_plan.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/evidence.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py`
- `python3 -m prefect_grace.cli plan-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --json --limit 10`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN/EXECUTION_PACKET.md --json`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/targeted_pytest.txt
- EVIDENCE/attempt-0001/compile_output.txt
- EVIDENCE/attempt-0001/lint_output.txt
- EVIDENCE/attempt-0001/cli_plan_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/scope_check.json

## Escalation Triggers
- Planner creates or edits an `EXECUTION_PACKET.yaml` sidecar.
- Planner scans arbitrary markdown fragments instead of exact `EXECUTION_PACKET.md` files.
- Invalid sidecars or missing project config are treated as scan failure.
- Root-level scan failures are reported as success.
- The command starts Prefect runs, live agents, Docker, backend, frontend, or Playwright.
