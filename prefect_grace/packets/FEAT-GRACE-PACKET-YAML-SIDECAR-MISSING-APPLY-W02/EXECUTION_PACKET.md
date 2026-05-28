# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02-CLI-COMMAND-SPLIT-SIDECAR

## Objective
Apply exactly one missing canonical `EXECUTION_PACKET.yaml` sidecar for the accepted CLI command module split packet, using the existing scoped sidecar migration command only.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02-CLI-COMMAND-SPLIT-SIDECAR`
- wave_id: `W02`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02-AGENT-API-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-CLI`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.yaml
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- all existing packet files except prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.yaml
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Use the existing `apply-packet-yaml-sidecar-migration` command only; do not implement or modify migration code.
- Apply only `FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT` by explicit `--packet-id` selection.
- The preflight must select exactly one `create` item for `prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.yaml`.
- The preflight selected item must report current source hash `sha256:0051515021fba7d381b81ed5a9ec95b37ef5f380ae778a18c31331ae5b2fd7d3` and planned source hash `sha256:91ade763366cbab5aaf25e269c22aa6c3c0f2e18b0fd09e8c3737590c64ec1f5`.
- The apply must write exactly `prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.yaml`.
- Do not reconcile the target runtime registry source hash in this packet.
- Post-apply `packet-status` for the target must still report accepted runtime source hash `sha256:0051515021fba7d381b81ed5a9ec95b37ef5f380ae778a18c31331ae5b2fd7d3`.
- Post-apply `sync-packets --dry-run --json` must report `changed_after_acceptance` containing exactly `FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT`; before review/bootstrap it may also report this newly-created W02 packet as `ready`.
- Do not mutate packet markdown, runtime registry files, executor history, backend, frontend, Docker, Playwright, live Prefect state, or live agents.
- Sidecar audit, migration plan, sync, packet status, validation, scope, and diff checks after apply are read-only.
- No Docker, backend, frontend, Playwright, live Prefect, or live agents are used by this packet.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture explicit preflight dry-run JSON for the target packet.
- Stop before apply if preflight target, path, action, risk, or source hashes differ from the expected values.
- Run the approved scoped apply once with `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change`.
- Capture apply JSON proving exactly one target sidecar write and no markdown, registry, Prefect run, or live-agent mutations.
- Capture post-audit JSON proving `invalid_sidecar=0`, `stale_sidecar=0`, and the target missing sidecar became canonical.
- Capture post-plan JSON proving remaining migration work is missing sidecars only and the target packet is absent from remaining items and findings.
- Capture post `sync-packets --dry-run --json` evidence proving the expected target-only `changed_after_acceptance` state.
- Capture target packet runtime status before any source-hash reconcile.
- Capture self-sidecar sync dry-run for this packet showing noop.
- Capture strict packet validation, evidence manifest validation, explicit scope check, and `git diff --check`.

## Verification
- `python3 -m prefect_grace.cli apply-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --packet-id FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT --dry-run --limit 1 --json`
- `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change python3 -m prefect_grace.cli apply-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --packet-id FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT --apply --limit 1 --i-understand-source-hash-change --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli plan-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --json --limit 100`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT-W01-CLI-COMMAND-MODULE-SPLIT --json`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EXECUTION_PACKET.md --repo-root . --json --changed-file prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.yaml --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EXECUTION_PACKET.md --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EXECUTION_PACKET.yaml --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/evidence_manifest.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/SUMMARY.md --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/preflight_explicit_packet_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/apply_one_sidecar.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/post_audit.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/post_plan.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/sync_packets_after_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/packet_status_target_before_reconcile.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/strict_validate_packet.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/validate_evidence_manifest.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/scope_check.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W02/EVIDENCE/attempt-0001/diff_check.txt`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/preflight_explicit_packet_dry_run.json
- EVIDENCE/attempt-0001/apply_one_sidecar.json
- EVIDENCE/attempt-0001/post_audit.json
- EVIDENCE/attempt-0001/post_plan.json
- EVIDENCE/attempt-0001/sync_packets_after_dry_run.json
- EVIDENCE/attempt-0001/packet_status_target_before_reconcile.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Preflight selects anything other than the target packet, target sidecar path, expected hashes, `create` action, and `accepted_source_hash_change` risk.
- Apply writes any path except `prefect_grace/packets/FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT/EXECUTION_PACKET.yaml`.
- Apply reports markdown mutations, registry mutations, Prefect runs, or live agents.
- Post-audit reports `invalid_sidecar` or `stale_sidecar`.
- Post-plan still includes the target packet or includes non-missing-sidecar migration work.
- Post `sync-packets --dry-run --json` reports any `changed_after_acceptance` item other than the target packet.
- Target runtime packet status no longer reports accepted source hash `sha256:0051515021fba7d381b81ed5a9ec95b37ef5f380ae778a18c31331ae5b2fd7d3` before a later reconcile packet.
- Any Docker, backend, frontend, Playwright, live Prefect, live agent, runtime registry file, executor history, packet markdown, ASTRO packet, or unrelated dirty/untracked path is mutated.
