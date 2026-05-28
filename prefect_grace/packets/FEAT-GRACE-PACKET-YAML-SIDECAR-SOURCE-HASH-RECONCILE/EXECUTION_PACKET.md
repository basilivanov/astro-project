# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W01-ONE-ACCEPTED-PACKET

## Objective
Reconcile exactly one accepted packet runtime registry source hash after accepted YAML sidecar canonicalization, using the existing scoped `registry-bootstrap-apply` command only.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W01-ONE-ACCEPTED-PACKET`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY-W01-ONE-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-CLI`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/**
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Use the existing scoped `registry-bootstrap-apply` command only for runtime registry reconciliation.
- Reconcile only `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- The preflight must plan exactly one runtime update for `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- The apply must update the runtime registry source hash from `sha256:15439d11b8a540d6feaba54a082d17e40da52d6c54171597901ff590e0977513` to `sha256:5ac1ba1641ef1df3b1b8d166d8b8c84740daf3b94b40f3cabd252845a721c890`.
- After apply, `packet-status` must report `registry_status=accepted` and source hash `sha256:5ac1ba1641ef1df3b1b8d166d8b8c84740daf3b94b40f3cabd252845a721c890`.
- After apply, `sync-packets --dry-run --json` must not list `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR` in `changed_after_acceptance`.
- No source files outside this packet directory may be modified.
- No markdown mutations, no source mutations, no Prefect runs, and no live agents may occur.
- No writes outside the runtime state root may occur except the command's own runtime backup if reported.
- Docker, backend, frontend, Playwright, broad corpus apply, live Prefect, and live agents remain untouched.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture preflight dry-run JSON for the scoped runtime registry update.
- Stop before applying if preflight does not report exactly one planned `update` for `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- Run the scoped runtime apply once for `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- Capture post-apply `packet-status` JSON proving accepted status and the reconciled source hash.
- Capture post-apply `sync-packets --dry-run --json` proving `changed_after_acceptance` no longer contains the reconciled packet id.
- Capture self-sidecar sync dry-run, strict packet validation, evidence manifest validation, scope check, and `git diff --check`.

## Verification
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR --dry-run --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR --apply --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EXECUTION_PACKET.md --repo-root . --json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EXECUTION_PACKET.md --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EXECUTION_PACKET.yaml --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/evidence_manifest.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/SUMMARY.md --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/preflight_registry_bootstrap_apply_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/apply_registry_bootstrap_apply.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/packet_status_after.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/sync_packets_after_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/strict_validate_packet.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/validate_evidence_manifest.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/scope_check.json --changed-file prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/EVIDENCE/attempt-0001/diff_check.txt`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/preflight_registry_bootstrap_apply_dry_run.json
- EVIDENCE/attempt-0001/apply_registry_bootstrap_apply.json
- EVIDENCE/attempt-0001/packet_status_after.json
- EVIDENCE/attempt-0001/sync_packets_after_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Preflight planned update count is not exactly one.
- Preflight or apply target is not `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- The scoped apply reports source mutations, markdown mutations, Prefect runs, live agents, or writes outside runtime state root beyond an explicit runtime backup.
- Post-apply `packet-status` does not report accepted status and source hash `sha256:5ac1ba1641ef1df3b1b8d166d8b8c84740daf3b94b40f3cabd252845a721c890`.
- Post-apply `sync-packets --dry-run --json` still reports `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR` in `changed_after_acceptance`.
- Any source file outside `prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE/**` is modified by this packet.
