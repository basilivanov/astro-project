# FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-PLAN-W01-SOURCE-HASH-IMPACT

## Summary
Implemented read-only `plan-packet-yaml-sidecar-migration` support.

Changed behavior:
- Adds `prefect_grace.platform.packet_yaml_sidecar_migration_plan.plan_packet_yaml_sidecar_migration`.
- Adds CLI command `python3 -m prefect_grace.cli plan-packet-yaml-sidecar-migration [--packet-root ...] [--project ...] [--json] [--limit N]`.
- Computes current and planned parser source hashes without writing temporary or real sidecars.
- Reads runtime registry status when project config loads; missing project config emits a warning and uses null `registry_status`.
- Emits create/update items only for `no_sidecar` and `stale_sidecar` packets.
- Counts canonical packets without including them in plan items.
- Records invalid sidecars and skipped packets as bounded findings with `ok=true` when the scan completes.
- Always reports `writes: []`, `source_mutations: []`, `prefect_runs_created: 0`, and `live_agents_started: 0`.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_yaml_sidecar_migration_plan.py tests/test_prefect_grace_cli_contracts.py -q`: PASS, 48 passed.
- `python3 -m compileall -q prefect_grace/platform/packet_parser.py prefect_grace/platform/packet_yaml_sidecar_migration_plan.py prefect_grace/cli_commands/evidence.py prefect_grace/cli_commands/parser.py`: PASS.
- `python3 scripts/grace_lint.py ...`: PASS for all four touched Python modules.
- `python3 -m prefect_grace.cli plan-packet-yaml-sidecar-migration --packet-root prefect_grace/packets --project prefect_grace/project.yaml --json --limit 10`: PASS.
- `python3 -m prefect_grace.cli validate-packet ... --strict --json`: PASS.
- `python3 -m prefect_grace.cli check-scope ... --json`: PASS.
- `python3 -m prefect_grace.cli validate-evidence-manifest ... --json`: PASS.
- `git diff --check`: PASS.

## Dry-Run Evidence
Corpus plan result:
- `ok: true`
- `packets_total: 70`
- counts: `canonical: 3`, `no_sidecar: 64`, `stale_sidecar: 1`, `invalid_sidecar: 0`, `skipped: 2`
- `plan_count: 65`
- `risk_counts: {"accepted_source_hash_change": 65}`
- `items_truncated: true` with `full_item_count: 65`
- `writes: []`, `source_mutations: []`, `prefect_runs_created: 0`, `live_agents_started: 0`

The accepted-source-hash impact is expected: the planner reports the migration blast radius before any sidecar mass-write.

## Observability Verdict
`clean`

Evidence reviewed after PASS:
- Targeted pytest output shows all selected tests passed.
- Corpus dry-run JSON shows no writes, source mutations, Prefect runs, or live agents.
- Corpus dry-run JSON shows all planned items are source-hash changing accepted registry entries.
- Strict packet validation JSON shows `ok: true`.
- Scope check JSON shows no outside-allowed or frozen-scope violations.

No backend, Docker, frontend, Playwright, live Prefect, or live agent flows were started.
