# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02-AGENT-API-SIDECAR

## Objective
Reconcile exactly one accepted Agent API failure-classifier runtime registry source hash after accepted YAML sidecar canonicalization, using the existing scoped `registry-bootstrap-apply` command only.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02-AGENT-API-SIDECAR`
- wave_id: `W02`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W01-ONE-GRACE-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-CLI`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-*/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/**
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Use the existing scoped `registry-bootstrap-apply` command only for runtime registry reconciliation.
- Reconcile only `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`.
- The preflight must plan exactly one runtime update for `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`.
- The apply must update the runtime registry source hash from `sha256:760c9c28f6576401349adc7e85aa42394902acbd7c2fe7beda9d1ba358e58ec6` to `sha256:f967a5db6ee0b8abb6ce779278b460e0942387c641640ee9309f3830f74f9e6f`.
- After apply, `packet-status` must report `registry_status=accepted` and source hash `sha256:f967a5db6ee0b8abb6ce779278b460e0942387c641640ee9309f3830f74f9e6f`.
- After target apply, `sync-packets --dry-run --json` must report `changed_after_acceptance=[]` and `registry_updates=0`.
- Before reviewer acceptance/bootstrap of this newly-created W02 packet, `sync-packets --dry-run --json` may report `ready=["FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02-AGENT-API-SIDECAR"]` and no other ready packets.
- Final reviewer/operator follow-up after accepting this W02 packet is to apply this W02 packet to the runtime registry with scoped `registry-bootstrap-apply`; only after that bootstrap step is `ready=[]` expected.
- `audit-packet-yaml-sidecars` must report no invalid or stale sidecars.
- Self-sidecar sync dry-run for this packet must be noop.
- No source files outside this packet directory may be modified.
- No markdown mutations, no source mutations, no Prefect runs, and no live agents may occur.
- No writes outside the runtime state root may occur.
- Docker, backend, frontend, Playwright, broad corpus apply, live Prefect, and live agents remain untouched.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture preflight dry-run JSON for the scoped runtime registry update.
- Stop before applying if preflight does not report exactly one planned `update` for `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`.
- Run the scoped runtime apply once for `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`.
- Capture post-apply `packet-status` JSON proving accepted status and the reconciled source hash.
- Capture post-target-apply `sync-packets --dry-run --json` proving `changed_after_acceptance=[]`, `registry_updates=0`, and pre-review `ready` contains exactly `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02-AGENT-API-SIDECAR`.
- Document that final `ready=[]` is expected only after reviewer acceptance and scoped runtime bootstrap of this W02 packet itself.
- Capture post-apply sidecar audit proving no invalid or stale sidecars.
- Capture self-sidecar sync dry-run, strict packet validation, evidence manifest validation, scope check, and `git diff --check`.

## Verification
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER --dry-run --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER --apply --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EXECUTION_PACKET.md --repo-root . --json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EXECUTION_PACKET.md --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EXECUTION_PACKET.yaml --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/evidence_manifest.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/SUMMARY.md --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/preflight_registry_bootstrap_apply_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/apply_registry_bootstrap_apply.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/packet_status_after.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/sync_packets_after_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/audit_sidecars_after.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/strict_validate_packet.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/validate_evidence_manifest.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/scope_check.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/EVIDENCE/attempt-0001/diff_check.txt`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/preflight_registry_bootstrap_apply_dry_run.json
- EVIDENCE/attempt-0001/apply_registry_bootstrap_apply.json
- EVIDENCE/attempt-0001/packet_status_after.json
- EVIDENCE/attempt-0001/sync_packets_after_dry_run.json
- EVIDENCE/attempt-0001/audit_sidecars_after.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Preflight planned update count is not exactly one.
- Preflight or apply target is not `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`.
- The scoped apply reports source mutations, markdown mutations, Prefect runs, live agents, or writes outside runtime state root.
- Post-apply `packet-status` does not report accepted status and source hash `sha256:f967a5db6ee0b8abb6ce779278b460e0942387c641640ee9309f3830f74f9e6f`.
- Post-target-apply `sync-packets --dry-run --json` does not report `changed_after_acceptance=[]` and `registry_updates=0`.
- Pre-review post-target-apply `sync-packets --dry-run --json` reports any ready packet other than `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02-AGENT-API-SIDECAR`.
- Post-apply sidecar audit reports invalid or stale sidecars.
- Any source file outside `prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W02/**` is modified by this packet.
