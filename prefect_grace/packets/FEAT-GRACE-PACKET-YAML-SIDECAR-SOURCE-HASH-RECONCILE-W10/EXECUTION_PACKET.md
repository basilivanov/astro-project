# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10-EVIDENCE-CONTRACTS-SIDECAR

## Objective
Reconcile exactly one accepted Evidence Contracts runtime registry source hash after accepted YAML sidecar creation, using the existing scoped `registry-bootstrap-apply` command only.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10-EVIDENCE-CONTRACTS-SIDECAR`
- wave_id: `W10`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W09-EVIDENCE-CONTRACTS-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-CLI`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.md
- prefect_grace/packets/FEAT-GRACE-EVIDENCE-CONTRACTS-MVP/EXECUTION_PACKET.yaml
- all existing packet files except prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/**
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Use the existing scoped `registry-bootstrap-apply` command only for runtime registry reconciliation.
- Reconcile only `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS`.
- Runtime mutation is allowed only through `registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS --apply --json`.
- Do not directly edit runtime YAML files.
- Do not mutate target source files or the target YAML sidecar.
- Do not create or update any missing sidecars outside this W10 packet.
- The preflight must plan exactly one runtime update for `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS`.
- The apply must update the runtime registry source hash from `sha256:279148232a2c210bcb27dd5b937e55d877ba8756d9dada5ccbc095e70d6a15a0` to `sha256:d0b71085098e495aed7e44ca36141c3695d7537a4fb75307eaf649013847b028`.
- After apply, `packet-status` must report `registry_status=accepted` and source hash `sha256:d0b71085098e495aed7e44ca36141c3695d7537a4fb75307eaf649013847b028`.
- After target apply, `sync-packets --dry-run --json` must report `changed_after_acceptance=[]`, `registry_updates=0`, `blocked=[]`, and `cascading_blocked=[]`.
- Before reviewer acceptance/bootstrap of this newly-created W10 packet, `sync-packets --dry-run --json` may report `ready=["FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10-EVIDENCE-CONTRACTS-SIDECAR"]`.
- `audit-packet-yaml-sidecars` must report `canonical=35`, `no_sidecar=55`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2`.
- Self-sidecar sync dry-run for this packet must be noop.
- No source mutations, no markdown mutations, no writes outside runtime state root, zero Prefect runs, and zero live agents.
- Docker, backend, frontend, Playwright, broad sidecar apply, live Prefect, live agents, provider APIs, commit, and push remain untouched.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture preflight dry-run JSON for the scoped runtime registry update.
- Stop before applying if preflight does not report exactly one planned update for `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS` from the expected old source hash to the expected new source hash.
- Run the scoped runtime apply once for `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS`.
- Capture post-apply `packet-status` JSON proving accepted status and the reconciled source hash.
- Capture post-target-apply `sync-packets --dry-run --json` proving `changed_after_acceptance=[]`, `registry_updates=0`, `blocked=[]`, and `cascading_blocked=[]`.
- Capture post-apply sidecar audit proving `canonical=35`, `no_sidecar=55`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2`.
- Capture self-sidecar sync dry-run, strict packet validation, evidence manifest validation, scope check with explicit changed W10 files, `git diff --check`, and a final assertion sweep in `SUMMARY.md`.

## Verification
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS --dry-run --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS --apply --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10/EXECUTION_PACKET.md --repo-root . --changed-file <each changed W10 file> --json`
- `git diff --check -- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W10`

## Expected Evidence
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/preflight_registry_bootstrap_apply_dry_run.json
- EVIDENCE/attempt-0001/approved_registry_bootstrap_apply.json
- EVIDENCE/attempt-0001/target_packet_status_after.json
- EVIDENCE/attempt-0001/sync_packets_after_target_apply.json
- EVIDENCE/attempt-0001/audit_sidecars_after.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Preflight planned update count is not exactly one.
- Preflight or apply target is not `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS`.
- Preflight or apply does not move the source hash from `sha256:279148232a2c210bcb27dd5b937e55d877ba8756d9dada5ccbc095e70d6a15a0` to `sha256:d0b71085098e495aed7e44ca36141c3695d7537a4fb75307eaf649013847b028`.
- The scoped apply reports source mutations, markdown mutations, Prefect runs, live agents, or writes outside runtime state root.
- Post-apply `packet-status` does not report accepted status and source hash `sha256:d0b71085098e495aed7e44ca36141c3695d7537a4fb75307eaf649013847b028`.
- Post-target-apply `sync-packets --dry-run --json` does not report `changed_after_acceptance=[]`, `registry_updates=0`, `blocked=[]`, and `cascading_blocked=[]`.
- Post-apply sidecar audit does not report `canonical=35`, `no_sidecar=55`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2`.
- Any target source file, target sidecar, missing sidecar, Docker, backend, frontend, Playwright, live Prefect, live agent, executor history, source runtime registry file, ASTRO packet, provider API, unrelated dirty/untracked path, commit, or push is mutated.
