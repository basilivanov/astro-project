# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT-W01-CORPUS-DRY-RUN-REPORT

## Objective
Add a non-mutating CLI audit that scans strict `EXECUTION_PACKET.md` packets under `prefect_grace/packets`, compares adjacent `EXECUTION_PACKET.yaml` sidecars against canonical parser payloads, and emits a bounded dry-run report before any corpus migration.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT-W01-CORPUS-DRY-RUN-REPORT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC-W01-DRY-RUN-APPLY`

## Impacted Modules
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-CLI`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/platform/packet_yaml_sidecar_audit.py
- prefect_grace/platform/packet_yaml_sidecar_sync.py
- prefect_grace/cli_commands/evidence.py
- prefect_grace/cli_commands/parser.py
- tests/test_prefect_grace_packet_yaml_sidecar_audit.py
- tests/test_prefect_grace_cli_contracts.py
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT/**

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
- Audit mode is read-only and must not create, update, or delete sidecars.
- Audit output always reports `writes: []`, `source_mutations: []`, `prefect_runs_created: 0`, and `live_agents_started: 0`.
- Discovery only includes files named exactly `EXECUTION_PACKET.md` below the packet root.
- Invalid sidecars are audit findings and do not fail the command when the packet root is readable.
- Missing or unreadable packet roots fail closed with `ok=false`.
- Runtime registry state, executor history, Prefect runs, live agents, backend, frontend, Docker, and Playwright remain untouched.

## Required Behavior
- Add `python3 -m prefect_grace.cli audit-packet-yaml-sidecars [--packet-root prefect_grace/packets] [--json] [--limit N]`.
- Default packet root is `prefect_grace/packets`.
- Classify discovered packets as `canonical`, `no_sidecar`, `stale_sidecar`, `invalid_sidecar`, or `skipped`.
- Build the desired canonical sidecar payload from strict markdown content without mutating sources.
- Report `packets_total`, counts by class, bounded examples per class, and bounded invalid-sidecar errors.
- Cap `--limit` at 100 and default it to 20.
- Return `ok=true` for completed audits even when invalid sidecars are found.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_yaml_sidecar_audit.py tests/test_prefect_grace_cli_contracts.py -q`
- `python3 -m compileall -q prefect_grace/platform/packet_yaml_sidecar_audit.py prefect_grace/cli_commands/evidence.py prefect_grace/cli_commands/parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_yaml_sidecar_audit.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/evidence.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 10`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-AUDIT/EXECUTION_PACKET.md --json`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/targeted_pytest.txt
- EVIDENCE/attempt-0001/compile_output.txt
- EVIDENCE/attempt-0001/lint_output.txt
- EVIDENCE/attempt-0001/cli_audit_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/scope_check.json

## Escalation Triggers
- Audit creates or edits an `EXECUTION_PACKET.yaml` sidecar.
- Audit scans arbitrary markdown fragments instead of exact `EXECUTION_PACKET.md` files.
- Invalid sidecars are treated as execution failure instead of findings.
- Root-level scan failures are reported as success.
- The command starts Prefect runs, live agents, Docker, backend, frontend, or Playwright.
