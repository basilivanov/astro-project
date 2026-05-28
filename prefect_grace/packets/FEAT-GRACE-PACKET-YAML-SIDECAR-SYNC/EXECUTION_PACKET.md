# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC-W01-DRY-RUN-APPLY

## Objective
Add a guarded CLI tool that generates or synchronizes canonical `EXECUTION_PACKET.yaml` sidecars for selected strict `EXECUTION_PACKET.md` packets without mutating markdown, runtime registry state, or unrelated packet artifacts.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC-W01-DRY-RUN-APPLY`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR, FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER-W01-SCOPED-APPLY`

## Impacted Modules
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-CLI`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/platform/packet_yaml_sidecar_sync.py
- prefect_grace/platform/packet_parser.py
- prefect_grace/cli_commands/evidence.py
- prefect_grace/cli_commands/parser.py
- tests/test_prefect_grace_packet_yaml_sidecar_sync.py
- tests/test_prefect_grace_packet_parser.py
- tests/test_prefect_grace_cli_contracts.py
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC/**

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
- Markdown packet files are never rewritten by the sidecar sync tool.
- Dry-run is the default and performs zero file writes.
- Apply mode writes only adjacent `EXECUTION_PACKET.yaml` files for explicitly requested packet paths.
- Existing invalid sidecars fail closed and are not overwritten unless a future packet defines an explicit repair mode.
- Generated sidecars use only canonical parser fields and are accepted by `parse_packet_markdown(Path(".../EXECUTION_PACKET.md"))`.
- Runtime registry state, executor history, Prefect runs, live agents, backend, frontend, Docker, and Playwright remain untouched.

## Required Behavior
- Add `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet <EXECUTION_PACKET.md> [--packet ...] [--dry-run|--apply] [--json]`.
- Require at least one `--packet`; blank or non-`EXECUTION_PACKET.md` paths fail closed.
- Default to dry-run when neither `--dry-run` nor `--apply` is provided.
- Report per-packet `planned_action`: `create`, `update`, `noop`, or `error`.
- Report `writes` and `markdown_mutations`; `markdown_mutations` must always be empty.
- Treat already canonical sidecars as `noop`.
- Treat valid but stale sidecars as `update` in dry-run and overwrite only under `--apply`.
- Treat malformed, unknown-field, packet-id-mismatched, or non-mapping sidecars as `error` with no write.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_yaml_sidecar_sync.py tests/test_prefect_grace_packet_parser.py tests/test_prefect_grace_cli_contracts.py`
- `python3 -m compileall -q prefect_grace/platform/packet_yaml_sidecar_sync.py prefect_grace/platform/packet_parser.py prefect_grace/cli_commands/evidence.py prefect_grace/cli_commands/parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_yaml_sidecar_sync.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_parser.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/evidence.py`
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC/EXECUTION_PACKET.md --dry-run --json`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/targeted_pytest.txt
- EVIDENCE/attempt-0001/compile_output.txt
- EVIDENCE/attempt-0001/lint_output.txt
- EVIDENCE/attempt-0001/cli_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/scope_check.json

## Escalation Triggers
- The tool rewrites markdown packet content.
- The tool can write outside the adjacent packet directory.
- Invalid existing sidecars are silently overwritten.
- Dry-run creates or edits files.
- Parser source hashes do not change after sidecar creation.
- The command accepts broad glob migration without explicit packet paths.
