# Execution Packet: FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR

## Objective
Introduce a canonical `EXECUTION_PACKET.yaml` sidecar contract for GRACE execution packets while preserving markdown-only packet parsing as the legacy fallback.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-CONTRACT`
- packet_id: `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`
- wave_id: `W01`
- status: `ready_for_review`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REVIEW-YAML-FIRST-DISCOVERY-W01-LAYOUT-HELPERS, FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-PACKET-FILTER-W01-SCOPED-APPLY`

## Impacted Modules
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/platform/packet_parser.py
- tests/test_prefect_grace_packet_parser.py
- tests/test_prefect_grace_controller_backlog_bootstrap.py
- tests/test_prefect_grace_registry_source_integrity_audit.py
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/**

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
- Existing markdown-only packet hashes remain unchanged.
- Existing `parse_packet_markdown` public imports and consumer call sites remain compatible.
- Invalid canonical sidecars fail closed instead of falling back silently.
- Runtime registry state and unrelated packet artifacts remain untouched.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_parser.py tests/test_prefect_grace_controller_backlog_bootstrap.py tests/test_prefect_grace_registry_source_integrity_audit.py tests/test_prefect_grace_cli_contracts.py`
- `python3 -m compileall -q prefect_grace/platform/packet_parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_parser.py`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EVIDENCE/attempt-0001 --json`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md

## Escalation Triggers
- YAML sidecar metadata can be ignored when present.
- YAML and markdown packet ids can diverge without a strict validation failure.
- Sidecar dependency or scope changes do not affect `ParsedPacket.source_hash`.
- Markdown-only source hashes change for existing packets.
- Bootstrap dependency planning still relies only on markdown regex bullets.
