# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY-W01-ONE-SIDECAR

## Objective
Apply exactly one stale canonical `EXECUTION_PACKET.yaml` sidecar through the accepted operator-gated migration command, without migrating missing sidecars.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY-W01-ONE-SIDECAR`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-APPLY-W01-STALE-ONLY-GATE`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-CLI`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/**

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
- Only the stale `prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml` sidecar may be updated by the migration apply.
- The 64 packets without sidecars must remain unmigrated.
- The apply command must use `--stale-only --apply --limit 1`, the explicit source-hash-change acknowledgement flag, and `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change`.
- Apply output must report no markdown mutations, registry mutations, Prefect runs, or live agents.
- Audit and plan verification must be read-only and report no writes, runs, or agents.
- Docker, backend, frontend, Playwright, live Prefect, and live agents remain untouched.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture a preflight stale-only dry-run proving `selected_count=1` and the target packet id is `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- Stop before applying if the selected dry-run target differs from `prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml`.
- Run the approved stale-only limit-1 apply command exactly once when preflight matches.
- Capture post-apply audit proving `stale_sidecar=0`, `invalid_sidecar=0`, canonical count increased by one, and no writes/runs/agents occurred in audit.
- Capture post-plan evidence proving no `stale_sidecar` work remains.
- Capture self-sidecar sync dry-run evidence for this packet showing noop.

## Verification
- `python3 -m prefect_grace.cli apply-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --stale-only --dry-run --limit 1 --json`
- `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change python3 -m prefect_grace.cli apply-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --stale-only --apply --limit 1 --i-understand-source-hash-change --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli plan-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY/EXECUTION_PACKET.md --repo-root . --json`
- `git diff --check`

## Expected Evidence
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/preflight_stale_only_dry_run.json
- EVIDENCE/attempt-0001/apply_stale_only_one_sidecar.json
- EVIDENCE/attempt-0001/post_audit.json
- EVIDENCE/attempt-0001/post_plan.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Dry-run selection is not exactly `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`.
- Apply would write any path other than `prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml`.
- Apply would create missing sidecars or mutate markdown, runtime registry, executor history, Prefect state, Docker, backend, frontend, or Playwright.
- Post-apply audit still reports a stale or invalid sidecar.
- Evidence cannot prove the apply had zero Prefect runs and zero live agents.
