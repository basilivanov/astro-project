# FEAT-GRACE-PACKET-YAML-SIDECAR-SYNC-W01-DRY-RUN-APPLY

## Summary
Implemented guarded `sync-packet-yaml-sidecar` dry-run/apply support.

Changed behavior:
- Generates canonical `EXECUTION_PACKET.yaml` payloads from strict markdown-only parser metadata.
- Defaults to dry-run and reports per-packet `create`, `update`, `noop`, or `error`.
- Applies only adjacent sidecars for explicitly requested `EXECUTION_PACKET.md` paths.
- Never rewrites markdown; results always include `markdown_mutations: []`.
- Fails closed for malformed, non-mapping, unknown-field, and packet-id-mismatched existing sidecars.

## Verification
- `python3 -m pytest -q tests/test_prefect_grace_packet_yaml_sidecar_sync.py tests/test_prefect_grace_packet_parser.py tests/test_prefect_grace_cli_contracts.py`: PASS, 56 passed.
- `python3 -m compileall -q prefect_grace/platform/packet_yaml_sidecar_sync.py prefect_grace/platform/packet_parser.py prefect_grace/cli_commands/evidence.py prefect_grace/cli_commands/parser.py`: PASS.
- `python3 scripts/grace_lint.py ...`: PASS for all four touched Python modules.
- `python3 -m prefect_grace.cli validate-packet ... --strict --json`: PASS.
- `python3 -m prefect_grace.cli sync-packet-yaml-sidecar ... --dry-run --json`: PASS, planned `noop`, no writes, no markdown mutations.
- `python3 -m prefect_grace.cli check-scope ... --json`: PASS, no outside-allowed or frozen violations.
- `git diff --check`: PASS.

## Observability Verdict
`clean`

Evidence reviewed after PASS:
- Targeted pytest output shows all selected tests passed.
- CLI dry-run JSON shows `planned_action: noop`, `writes: []`, `markdown_mutations: []`, and no errors.
- Strict packet validation JSON shows `ok: true` with updated sidecar-inclusive `source_hash`.
- Scope check JSON shows `outside_allowed: []`, `frozen_violations: []`, and `invalid_paths: []`.

No backend, Docker, frontend, Playwright, live Prefect, or live agent flows were started.
