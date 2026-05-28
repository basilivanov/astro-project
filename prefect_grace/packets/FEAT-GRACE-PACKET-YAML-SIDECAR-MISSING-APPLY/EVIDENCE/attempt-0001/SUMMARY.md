# FEAT-GRACE-PACKET-YAML-SIDECAR-MISSING-APPLY attempt-0001

## Summary
Applied the explicit one-packet missing sidecar command for `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`, but the post-test observability gate is not clean.

## Preflight
- Command: `apply-packet-yaml-sidecar-migration --packet-id FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER --dry-run --limit 1 --json`
- selected_count: 1
- target packet_id: `FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`
- target sidecar: `prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/EXECUTION_PACKET.yaml`
- planned_action: `create`
- current_source_hash: `sha256:760c9c28f6576401349adc7e85aa42394902acbd7c2fe7beda9d1ba358e58ec6`
- planned_source_hash: `sha256:f967a5db6ee0b8abb6ce779278b460e0942387c641640ee9309f3830f74f9e6f`
- risk: `accepted_source_hash_change`
- writes/source_mutations/markdown_mutations/registry_mutations: []
- prefect_runs_created/live_agents_started: 0/0

## Apply
- Command used `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change`, `--packet-id`, `--apply`, `--limit 1`, and `--i-understand-source-hash-change`.
- ok: true
- selected_count: 1
- writes: [`prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/EXECUTION_PACKET.yaml`]
- source_mutations: [`prefect_grace/packets/FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP/EXECUTION_PACKET.yaml`]
- markdown_mutations: []
- registry_mutations: []
- prefect_runs_created/live_agents_started: 0/0

## Post-Apply Audit
- packets_total: 74
- canonical: 8
- no_sidecar: 63
- stale_sidecar: 0
- invalid_sidecar: 1
- skipped: 2
- audit writes/source_mutations: []
- audit prefect_runs_created/live_agents_started: 0/0
- unexpected degradation: the new target sidecar is reported invalid because the target markdown title is `# Execution Packet: GRACE Agent API Failure Classification MVP`, which contributes a markdown packet id `GRACE` before the `packet_id` metadata line.

## Post-Apply Plan
- plan_count: 63
- risk_counts: `accepted_source_hash_change=63`
- stale_sidecar: 0
- invalid_sidecar: 1
- remaining plan items are missing sidecars, and the target packet is not in remaining plan items.

## Sync Packets
- `sync-packets --dry-run --json` exited non-zero.
- Error: `YAML sidecar packet_id does not match markdown packet_id: FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER != GRACE`
- Expected degraded state with one `changed_after_acceptance` could not be proven because parsing stops on the target sidecar mismatch.

## Verification
- Strict packet validation for this new packet: pass.
- Self-sidecar sync dry-run: noop.
- Evidence manifest validation: see `validate_evidence_manifest.json`.
- Scope check: see `scope_check.json`.
- `git diff --check`: see `diff_check.txt`.

## Observability Verdict
unexpected-degradation. The explicit apply was scoped to one GRACE sidecar and did not mutate markdown, registry, Docker, backend, frontend, Playwright, Prefect runs, or live agents. The required post-state is not achieved because the existing sidecar parser rejects the target markdown/sidecar pair after creation.
