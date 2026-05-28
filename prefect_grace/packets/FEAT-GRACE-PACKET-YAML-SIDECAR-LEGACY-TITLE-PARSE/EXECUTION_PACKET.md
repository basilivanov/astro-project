# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE-W01-HEADING-ID-GUARD

## Objective
Fix packet markdown parsing so descriptive legacy H1 titles after `Execution Packet:` do not create false markdown packet id mismatches when explicit packet metadata exists, while preserving strict sidecar mismatch detection against explicit metadata.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE-W01-HEADING-ID-GUARD`
- wave_id: `W01`
- status: `ready_for_review`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W01-ONE-ACCEPTED-PACKET`

## Impacted Modules
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-PACKET-YAML-SIDECAR`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/platform/packet_parser.py
- tests/test_prefect_grace_packet_parser.py
- tests/test_prefect_grace_packet_yaml_sidecar_audit.py
- tests/test_prefect_grace_packet_yaml_sidecar_migration_plan.py
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY/**

## Must Preserve
- Explicit markdown `packet_id` metadata remains authoritative for strict packets.
- YAML sidecar `packet_id` mismatch against explicit markdown metadata still fails closed.
- Existing H1 packet ids that look like controller packet ids still seed `packet_id`.
- Descriptive H1 text remains available as packet title when it is not a packet id.
- No Docker, backend, frontend, Playwright, live Prefect, or live agent commands are run.
- Existing unrelated dirty and untracked files are not reverted or modified.

## Required Behavior
- Add a narrow helper that recognizes real controller packet id candidates from H1 text.
- Treat H1 `Execution Packet:` text that does not look like a packet id as a title only.
- Keep explicit bullet/header metadata in the markdown id set used for sidecar mismatch checks.
- Keep canonical YAML sidecar audit and sync dry-runs free of the legacy `GRACE` mismatch.
- Unblock the separate missing-sidecar apply rework by removing false H1-derived sidecar mismatches.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_parser.py tests/test_prefect_grace_packet_yaml_sidecar_audit.py tests/test_prefect_grace_packet_yaml_sidecar_migration_plan.py`
- `python3 -m compileall -q prefect_grace/platform/packet_parser.py`
- `python3 scripts/grace_lint.py prefect_grace/platform/packet_parser.py`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE/EVIDENCE/attempt-0003/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-LEGACY-TITLE-PARSE/EXECUTION_PACKET.md --json`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0003/evidence_manifest.json
- EVIDENCE/attempt-0003/SUMMARY.md
- EVIDENCE/attempt-0003/previous_targeted_pytest.txt
- EVIDENCE/attempt-0003/strict_validate_packet.json
- EVIDENCE/attempt-0003/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0003/validate_evidence_manifest.json
- EVIDENCE/attempt-0003/scope_check.json
- EVIDENCE/attempt-0003/diff_check.txt

## Escalation Triggers
- Sidecar mismatch detection is weakened for explicit markdown metadata.
- H1 FEAT packet ids stop populating packet id for strict packets.
- The audit still reports `invalid_sidecar` for the dirty AGENT API sidecar due to `GRACE`.
- The sync dry-run fails or reports the legacy `GRACE` mismatch.
- Verification requires Docker, backend, frontend, Playwright, live Prefect, or live agent commands.
