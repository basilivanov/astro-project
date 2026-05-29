# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15-MANAGED-PACKET-RUNNER-SIDECAR

## Objective
Create the missing canonical YAML sidecar for the accepted Managed Packet Runner packet, without reconciling the accepted runtime source hash in this packet.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15-MANAGED-PACKET-RUNNER-SIDECAR`
- wave_id: `W15`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W14-EXECUTOR-REGISTRY-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-PACKET-YAML-SIDECAR`
- `M-GRACE-CLI`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/**
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.yaml

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/REVIEWS/**
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EVIDENCE/**
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/SUMMARY.md
- all existing packet files except prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.yaml and prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/**
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Create only the missing adjacent YAML sidecar for `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER`.
- Do not mutate the target `EXECUTION_PACKET.md`.
- Do not reconcile the target runtime source hash in this packet.
- The target runtime source hash before sidecar creation is `sha256:fdda272d31675f6bfcef867494a425fbbe4de6f0a77db9866683081dd2afa313`.
- After target sidecar creation, `sync-packets --dry-run --json` must report `changed_after_acceptance` containing only `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER`, with `blocked=[]`, `cascading_blocked=[]`, and `registry_updates=0`.
- A follow-up source-hash reconcile packet must handle the accepted target runtime hash update.
- Final sidecar audit must report `canonical=50`, `no_sidecar=50`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2` if only the target sidecar and this packet sidecar are added.
- Self-sidecar sync dry-run for this packet must be noop.
- No source markdown mutations, no direct runtime YAML edits, no Prefect runs, no live agents, no Docker, no backend, no frontend, no Playwright, no provider APIs, no commit, and no push.

## Required Behavior
- Capture target strict validation before sidecar creation.
- Capture target sidecar sync preflight dry-run and require planned action `create`.
- Apply target sidecar creation using `sync-packet-yaml-sidecar --apply` for the target packet only.
- Capture target strict validation after sidecar creation and record the new source hash.
- Capture target `registry-bootstrap-apply --dry-run --json` proving exactly one planned accepted runtime registry update from the old source hash to the new source hash, without applying it.
- Capture `sync-packets --project prefect_grace/project.yaml --dry-run --json` proving the only changed accepted source hash is the target packet and there are no blocked or cascading-blocked packets.
- Capture sidecar audit, self-sidecar sync dry-run, strict packet validation, evidence manifest validation, scope check, `git diff --check`, and final assertion summary.

## Verification
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md --apply --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER --dry-run --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W15/EXECUTION_PACKET.md --repo-root . --changed-file <each changed file> --json`
- `git diff --check -- <changed files>`

## Expected Evidence
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/target_validate_before.json
- EVIDENCE/attempt-0001/target_sidecar_preflight_dry_run.json
- EVIDENCE/attempt-0001/target_sidecar_apply.json
- EVIDENCE/attempt-0001/target_validate_after.json
- EVIDENCE/attempt-0001/target_registry_bootstrap_apply_dry_run.json
- EVIDENCE/attempt-0001/sync_packets_after_target_sidecar.json
- EVIDENCE/attempt-0001/audit_sidecars_after.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Target sidecar preflight does not plan `create`.
- Target sidecar apply mutates markdown or any file outside `prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.yaml`.
- Target strict validation fails before or after sidecar creation.
- Target source hash does not change after sidecar creation.
- Target registry-bootstrap dry-run does not plan exactly one accepted update for `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER`.
- Final sync reports any `blocked`, `cascading_blocked`, registry update, or `changed_after_acceptance` outside the target packet.
- Final sidecar audit reports stale or invalid sidecars, or counts outside the expected bounded values.
- Self-sidecar sync dry-run is not noop.
- Evidence manifest validation, scope check, or `git diff --check` fails.
- Any frozen source, runtime registry YAML file, ASTRO packet, backend, frontend, Docker, Playwright, live Prefect, live agent, provider API, commit, or push is mutated.
