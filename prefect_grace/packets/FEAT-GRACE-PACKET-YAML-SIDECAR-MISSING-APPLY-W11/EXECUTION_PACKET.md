# Execution Packet: FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11-EVIDENCE-MANIFEST-PATH-RESOLUTION-SIDECAR

## Objective
Apply exactly one missing canonical `EXECUTION_PACKET.yaml` sidecar for the accepted Evidence Manifest Path Resolution packet, using the existing scoped sidecar sync command only.

## Slice
- feature_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY`
- packet_id: `FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11-EVIDENCE-MANIFEST-PATH-RESOLUTION-SIDECAR`
- wave_id: `W11`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-YAML-SIDECAR-SOURCE-HASH-RECONCILE-W11-EVIDENCE-MANIFEST-IDENTITY-GATE-SIDECAR`

## Impacted Modules
- `M-GRACE-PACKET-AUTHORING`
- `M-GRACE-CLI`
- `M-GRACE-PACKET-VALIDATION`

## Allowed Write Scope
- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/**
- prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-*/**
- prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.md
- all existing packet files except prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml
- /var/lib/grace-orchestrator/**/runs/**
- /var/lib/grace-orchestrator/**/agents/**

## Must Preserve
- Use only the existing `sync-packet-yaml-sidecar` command for the target sidecar creation.
- Apply only `prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml`.
- Do not mutate target markdown.
- Do not run `registry-bootstrap-apply --apply` for the target packet in this packet.
- Do not mutate runtime registry files or executor history.
- Do not mutate backend, frontend, ASTRO packet directories, Docker, Playwright, live Prefect state, or live agents.
- The preflight dry-run must plan exactly one `create` for the target sidecar and no markdown mutations.
- The target runtime source hash before sidecar creation is `sha256:8282373b1adf65930167c7a9132897083f76e901b686ae28e75c07a9be909c8c`.
- The target strict source hash before sidecar creation is `sha256:8282373b1adf65930167c7a9132897083f76e901b686ae28e75c07a9be909c8c`.
- The target validation after sidecar creation must record the actual post-sidecar source hash.
- After target sidecar creation, `sync-packets --dry-run --json` is expected to report `registry_updates=0`, `changed_after_acceptance` containing exactly `FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION-W01-MANIFEST-RELATIVE-ARTIFACTS`, and `ready` may include this packet before reviewer/runtime reconcile.
- After target sidecar creation and this packet self sidecar, `audit-packet-yaml-sidecars --json --limit 100` is expected to report `canonical=40`, `no_sidecar=53`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2`.
- Self-sidecar sync dry-run for this packet must be noop.
- No Docker, backend, frontend, Playwright, live Prefect, live agents, provider APIs, commit, or push are used by this packet.

## Required Behavior
- Create this strict execution packet and canonical YAML sidecar.
- Capture explicit preflight dry-run JSON for the target packet sidecar.
- Stop before apply if preflight does not plan exactly one `create` for `prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml`.
- Run the scoped target sidecar apply once.
- Capture apply JSON proving exactly the target sidecar was created and no markdown was mutated.
- Capture strict target packet validation after sidecar creation and record the new target source hash.
- Capture `sync-packets --dry-run --json` evidence showing the expected target-only `changed_after_acceptance` state before the next runtime source-hash reconcile package.
- Capture post-apply sidecar audit showing the expected sidecar counts.
- Capture self-sidecar sync dry-run, strict packet validation, evidence manifest validation, explicit scope check, `git diff --check`, and a final assertion sweep in `SUMMARY.md`.

## Verification
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.md --apply --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli sync-packets --project prefect_grace/project.yaml --dry-run --json`
- `python3 -m prefect_grace.cli audit-packet-yaml-sidecars --packet-root prefect_grace/packets --json --limit 100`
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/EXECUTION_PACKET.md --dry-run --json`
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/EXECUTION_PACKET.md --strict --json`
- `python3 -m prefect_grace.cli validate-evidence-manifest prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/EVIDENCE/attempt-0001/evidence_manifest.json --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/EXECUTION_PACKET.md --artifact-root prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/EVIDENCE/attempt-0001 --json`
- `python3 -m prefect_grace.cli check-scope --packet prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11/EXECUTION_PACKET.md --repo-root . --changed-file <each changed W11 file> --changed-file prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml --json`
- `git diff --check -- prefect_grace/packets/FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY-W11 prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml`

## Expected Evidence
- EVIDENCE/attempt-0001/SUMMARY.md
- EVIDENCE/attempt-0001/evidence_manifest.json
- EVIDENCE/attempt-0001/preflight_target_sidecar_dry_run.json
- EVIDENCE/attempt-0001/apply_target_sidecar.json
- EVIDENCE/attempt-0001/target_strict_validate_packet.json
- EVIDENCE/attempt-0001/sync_packets_after_target_apply.json
- EVIDENCE/attempt-0001/audit_sidecars_after.json
- EVIDENCE/attempt-0001/self_sidecar_sync_dry_run.json
- EVIDENCE/attempt-0001/strict_validate_packet.json
- EVIDENCE/attempt-0001/validate_evidence_manifest.json
- EVIDENCE/attempt-0001/scope_check.json
- EVIDENCE/attempt-0001/diff_check.txt

## Escalation Triggers
- Preflight plans anything other than one `create` for the target sidecar.
- Apply writes any path except `prefect_grace/packets/FEAT-GRACE-EVIDENCE-MANIFEST-PATH-RESOLUTION/EXECUTION_PACKET.yaml`.
- Apply reports markdown mutations, registry mutations, Prefect runs, live agents, or provider API use.
- Target validation fails after sidecar creation.
- Post-apply `sync-packets --dry-run --json` reports any `changed_after_acceptance` item other than the target packet, or reports runtime registry updates.
- Post-apply sidecar audit reports counts other than `canonical=40`, `no_sidecar=53`, `stale_sidecar=0`, `invalid_sidecar=0`, and `skipped=2`.
- Any Docker, backend, frontend, Playwright, live Prefect, live agent, runtime registry file, executor history, packet markdown, ASTRO packet, unrelated dirty/untracked path, commit, or push is mutated.
