# Execution Packet: FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01-REWORK-RESUME-GATE-ID

## Objective
Repair the stale dependency id in exactly two accepted GRACE packet markdown sources so YAML sidecar rollout can continue without dependency resolution drift.

## Slice
- feature_id: `FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR`
- packet_id: `FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01-REWORK-RESUME-GATE-ID`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W13-EXECUTOR-HISTORY-SCOPE-BLOCKED-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-RUNTIME-REGISTRY`
- `M-GRACE-CLI`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/**
- prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.md
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/REVIEWS/**
- prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EVIDENCE/**
- prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/SUMMARY.md
- prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.yaml
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/REVIEWS/**
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EVIDENCE/**
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/SUMMARY.md
- prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.yaml
- all existing packet files except the two target EXECUTION_PACKET.md files and prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/**
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Replace only `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-RESUME-GATE` with `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE` in the two target `EXECUTION_PACKET.md` files.
- Do not create `EXECUTION_PACKET.yaml` for `FEAT-GRACE-EXECUTOR-REGISTRY-MVP` or `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP`.
- Do not edit target packet reviews, evidence, summaries, or sidecars.
- Do not directly edit runtime YAML files.
- Runtime registry reconciliation is allowed only through the existing scoped `registry-bootstrap-apply` CLI and only for the two target packet ids.
- Do not create target sidecars in this packet.
- Do not run Docker, backend, frontend, Playwright, live Prefect, live agents, provider APIs, commit, or push.
- Ignore unrelated dirty or untracked paths, including `.worktrees/`, `prefect_grace/executor_history.yaml`, `prefect_grace/packet_registry.yaml`, and `prefect_grace/packets/FEAT-ASTRO-*/**`.
- After source repair, each target preflight must plan exactly one runtime registry source hash update from the old hash to the new hash.
- Final `sync-packets --dry-run --json` must report `changed_after_acceptance=[]`, `blocked=[]`, `cascading_blocked=[]`, and `registry_updates=0`; before reviewer acceptance/bootstrap it may report this repair packet as the only ready packet.
- Final `audit-packet-yaml-sidecars --json --limit 100` must report `canonical=45`, `no_sidecar=52`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2` if only this repair sidecar was added.
- Self-sidecar sync dry-run for this packet must be noop.

## Required Behavior
- Capture before and after strict `validate-packet --json` for both targets, proving the dependency id changed and source hashes changed.
- Capture `packet-status --json` for both targets before source repair and after runtime registry reconcile.
- After editing the two target markdown files, run scoped `registry-bootstrap-apply --dry-run --json` once per target and stop if either preflight is not exactly one target update from the recorded old hash to the computed new hash.
- Run scoped `registry-bootstrap-apply --apply --json` once per target only after the corresponding preflight is clean.
- Capture final `sync-packets --project prefect_grace/project.yaml --dry-run --json`.
- Capture final `audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`.
- Capture self-sidecar sync dry-run, strict validation for this repair packet, evidence manifest validation, scope check with explicit changed files, `git diff --check` over changed files, and a final assertion sweep in `SUMMARY.md`.
- The observability verdict in `SUMMARY.md` must be one of `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Verification
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY --json`
- `python3 -m prefect_grace.cli packet-status --project prefect_grace/project.yaml --packet-id FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY --dry-run --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER --dry-run --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY --apply --json`
- `python3 -m prefect_grace.cli registry-bootstrap-apply --project prefect_grace/project.yaml --packet-id FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER --apply --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-DEPENDENCY-ID-REPAIR-W01/EXECUTION_PACKET.md --repo-root . --changed-file <each changed file> --json`
- `git diff --check -- <changed files>`

## Expected Evidence
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/target_executor_registry_validate_before.json
- EVIDENCE/attempt-0001/target_managed_packet_runner_validate_before.json
- EVIDENCE/attempt-0001/target_executor_registry_validate_after.json
- EVIDENCE/attempt-0001/target_managed_packet_runner_validate_after.json
- EVIDENCE/attempt-0001/target_executor_registry_packet_status_before.json
- EVIDENCE/attempt-0001/target_managed_packet_runner_packet_status_before.json
- EVIDENCE/attempt-0001/target_executor_registry_packet_status_after.json
- EVIDENCE/attempt-0001/target_managed_packet_runner_packet_status_after.json
- EVIDENCE/attempt-0001/preflight_executor_registry_registry_bootstrap_apply_dry_run.json
- EVIDENCE/attempt-0001/preflight_managed_packet_runner_registry_bootstrap_apply_dry_run.json
- EVIDENCE/attempt-0001/approved_executor_registry_registry_bootstrap_apply.json
- EVIDENCE/attempt-0001/approved_managed_packet_runner_registry_bootstrap_apply.json
- EVIDENCE/attempt-0001/sync_packets_final_dry_run.json
- EVIDENCE/attempt-0001/audit_sidecars_final.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Any stale `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-RESUME-GATE` dependency remains in either target `EXECUTION_PACKET.md`.
- Any replacement changes text other than the exact stale dependency id in the two target packet files.
- Either target strict validation fails after source repair.
- Either target source hash does not change after dependency id repair.
- Either scoped preflight plans no update, more than one update, a non-target update, or an update from/to hashes other than the validated old and new target source hashes.
- Either scoped apply reports source file mutation, target sidecar mutation, Prefect runs, live agents, or writes outside the runtime state root.
- Post-reconcile `packet-status` for either target does not report `registry_status=accepted` and the new source hash.
- Final `sync-packets --dry-run --json` reports any `changed_after_acceptance`, `blocked`, `cascading_blocked`, or `registry_updates`.
- Final sidecar audit reports stale or invalid sidecars, or counts differing from the expected bounded repair counts without a documented blocker.
- `validate-evidence-manifest`, `check-scope`, or `git diff --check` fails.
- Docker, backend, frontend, Playwright, live Prefect, live agents, provider APIs, commit, push, target reviews/evidence/summaries, target sidecars, source runtime YAML files, ASTRO packets, or unrelated dirty/untracked paths are mutated.
