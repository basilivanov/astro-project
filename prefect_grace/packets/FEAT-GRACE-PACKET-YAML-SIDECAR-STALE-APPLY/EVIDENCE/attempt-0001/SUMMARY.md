# FEAT-GRACE-PACKET-YAML-SIDECAR-STALE-APPLY attempt-0001

## Summary
Applied exactly one stale canonical `EXECUTION_PACKET.yaml` sidecar using the accepted operator-gated stale-only migration apply path.

## Preflight
- Command: `apply-packet-yaml-sidecar-migration --stale-only --dry-run --limit 1 --json`
- selected_count: 1
- target packet_id: `FEAT-GRACE-PACKET-YAML-CONTRACT-W01-PACKET-SPEC-SIDECAR`
- target sidecar: `prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml`
- planned_action: `update`
- risk: `accepted_source_hash_change`
- writes/source_mutations: []

## Apply
- Command used `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change`, `--stale-only`, `--apply`, `--limit 1`, and `--i-understand-source-hash-change`.
- ok: true
- selected_count: 1
- writes: [`prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml`]
- source_mutations: [`prefect_grace/packets/FEAT-GRACE-PACKET-YAML-CONTRACT/EXECUTION_PACKET.yaml`]
- markdown_mutations: []
- registry_mutations: []
- prefect_runs_created: 0
- live_agents_started: 0

## Post-Apply Audit
- packets_total: 72
- canonical: 6
- no_sidecar: 64
- stale_sidecar: 0
- invalid_sidecar: 0
- skipped: 2
- audit writes/source_mutations: []
- audit prefect_runs_created/live_agents_started: 0/0

## Post-Apply Plan
- stale_sidecar: 0
- invalid_sidecar: 0
- plan_count: 64, all remaining work is missing sidecars.
- writes/source_mutations: []
- prefect_runs_created/live_agents_started: 0/0

## Verification
- Strict packet validation: pass.
- Evidence manifest validation: pass.
- Self-sidecar sync dry-run: noop.
- Scope check: pass.
- `git diff --check`: pass.

## Observability Verdict
clean. Evidence is deterministic local CLI evidence. Docker, backend, frontend, Playwright, live Prefect, and live agents were not used.
