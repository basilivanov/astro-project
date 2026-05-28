# FEAT-GRACE-PACKET-YAML-SIDECAR-MIGRATION-APPLY attempt-0001

## Summary
Implemented `apply-packet-yaml-sidecar-migration` as a bounded operator-gated apply path for canonical `EXECUTION_PACKET.yaml` sidecars.

## Safety behavior
- Default mode is dry-run.
- Real writes require `--apply`.
- Unfiltered migration apply is rejected with `SELECTION_REQUIRED`.
- Selection requires `--stale-only` or explicit `--packet-id`.
- Apply mode has default limit 1 and hard max limit 10.
- Source-hash-changing apply requires both `--i-understand-source-hash-change` and `GRACE_PACKET_YAML_MIGRATION_APPROVED=source_hash_change`.
- Writes are delegated to the existing sidecar sync module after preflight.
- Apply writes only adjacent `EXECUTION_PACKET.yaml` sidecars and reports those writes as `source_mutations`.

## Real corpus dry-run
- packets_total: 71
- plan_count: 65
- stale-only selected_count: 1
- source_hash_change_count: 1
- writes: []
- source_mutations: []
- prefect_runs_created: 0
- live_agents_started: 0

## Blocked bulk proof
Unfiltered `--apply` returns `ok=false`, `selected_count=0`, `SELECTION_REQUIRED`, and zero writes/runs/agents.

## Verification
- Targeted pytest: 51 passed.
- Compileall: pass.
- Targeted GRACE lint: pass.
- Strict packet validation: ok=true.
- Scope check: ok=true.
- `git diff --check`: pass.

## Observability Verdict
clean. Evidence is deterministic CLI/static/unit-test evidence. Real corpus apply was not run; Docker, backend, frontend, Playwright, live Prefect, and live agents were not used.
