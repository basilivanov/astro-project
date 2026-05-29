# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06-E2E-PREFECT-FLOW-SIDECAR

## Objective
Reconcile exactly one accepted E2E Prefect flow wiring runtime registry source hash after accepted YAML sidecar creation, using the existing scoped `registry-bootstrap-apply` command only.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06-E2E-PREFECT-FLOW-SIDECAR`
- wave_id: `W06`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W05-E2E-PREFECT-FLOW-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-CLI`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W05/**
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W05/**
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Use the existing scoped `registry-bootstrap-apply` command only for runtime registry reconciliation.
- Reconcile only `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW`.
- Runtime mutation is allowed only through `registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW --apply --json`.
- Do not directly edit runtime YAML files.
- Do not mutate target source files or the target YAML sidecar.
- Do not create or update any missing sidecars.
- The preflight must plan exactly one runtime update for `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW`.
- The apply must update the runtime registry source hash from `sha256:da80f844b235fe9541905d760e042e37c893e380196602b10813b0c8eeed01bb` to `sha256:ff72a18fee6aa415a6b087edffdc5e2d79a7a5dee962e6061371f7dd062079df`.
- After apply, `packet-status` must report `registry_status=accepted` and source hash `sha256:ff72a18fee6aa415a6b087edffdc5e2d79a7a5dee962e6061371f7dd062079df`.
- After target apply, `sync-packets --dry-run --json` must report `changed_after_acceptance=[]` and `registry_updates=0`.
- Before reviewer acceptance/bootstrap of this newly-created W06 packet, `sync-packets --dry-run --json` may report `ready=["FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06-E2E-PREFECT-FLOW-SIDECAR"]` and no other ready packets.
- `audit-packet-yaml-sidecars` must report no invalid or stale sidecars.
- Self-sidecar sync dry-run for this packet must be noop.
- No source mutations, no markdown mutations, no writes outside runtime state root, zero Prefect runs, and zero live agents.
- Docker, backend, frontend, Playwright, broad sidecar apply, live Prefect, and live agents remain untouched.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture preflight dry-run JSON for the scoped runtime registry update.
- Stop before applying if preflight does not report exactly one planned update for `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW` from the expected old source hash to the expected new source hash.
- Run the scoped runtime apply once for `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW`.
- Capture post-apply `packet-status` JSON proving accepted status and the reconciled source hash.
- Capture post-target-apply `sync-packets --dry-run --json` proving `changed_after_acceptance=[]`, `registry_updates=0`, and pre-review `ready` contains at most this W06 packet.
- Capture post-apply sidecar audit proving no invalid or stale sidecars.
- Capture self-sidecar sync dry-run, strict packet validation, evidence manifest validation, scope check, `git diff --check`, and a final assertion sweep in `SUMMARY.md`.

## Verification
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW --dry-run --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW --apply --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06/EXECUTION_PACKET.md --repo-root . --json`
- `git diff --check`

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
- Preflight or apply target is not `FEAT-GRACE-E2E-PREFECT-FLOW-WIRING-MVP-W01-E2E-PREFECT-FLOW`.
- Preflight or apply does not move the source hash from `sha256:da80f844b235fe9541905d760e042e37c893e380196602b10813b0c8eeed01bb` to `sha256:ff72a18fee6aa415a6b087edffdc5e2d79a7a5dee962e6061371f7dd062079df`.
- The scoped apply reports source mutations, markdown mutations, Prefect runs, live agents, or writes outside runtime state root.
- Post-apply `packet-status` does not report accepted status and source hash `sha256:ff72a18fee6aa415a6b087edffdc5e2d79a7a5dee962e6061371f7dd062079df`.
- Post-target-apply `sync-packets --dry-run --json` does not report `changed_after_acceptance=[]` and `registry_updates=0`.
- Pre-review post-target-apply `sync-packets --dry-run --json` reports any ready packet other than `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W06-E2E-PREFECT-FLOW-SIDECAR`.
- Post-apply sidecar audit reports invalid or stale sidecars.
- Any target source file, target sidecar, missing sidecar, Docker, backend, frontend, Playwright, live Prefect, live agent, executor history, source runtime registry file, ASTRO packet, or unrelated dirty/untracked path is mutated.
