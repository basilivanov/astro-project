# Review 0001 - FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET

status: accepted
reviewer: codex
source_hash: sha256:937705462c1b06120af7e4ec44f5864d91ca725923f0d5a9b8d324c808c04df0
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

accepted

## What Passed

- Live-agent execution is behind all required gates: `--execute-agent`,
  `--i-understand-live-agent`, and `GRACE_LIVE_AGENT_OPT_IN=single-scratch`.
- Missing gates fail before temp root reset, Prefect submission, or agent
  launch, with `agent_launch_count=0`.
- Root validation rejects unsafe, broad, repo-contained, and overlapping temp
  roots before destructive cleanup.
- The synthetic packet is deterministic, selected through registry-aware
  planning, and scoped to
  `scratch/grace-live-opt-in-single-scratch/**`.
- Multi-packet ready plans fail closed.
- Injected live path records exactly one launch with `dry_run=false` and
  `execute_agent=true`.
- Scope failure blocks `ok=true`.
- Reviewer hardening added one regression: even if an injected runner reports
  `scope_verdict=passed`, `changed_files` are independently checked through
  `scope_guard`; product/frozen paths now fail with
  `LIVE_OPT_IN_CHANGED_FILES_OUTSIDE_SCRATCH`.
- CLI JSON envelope preserves `ok`, `project_key`, `command`, `result`,
  `data`, `warnings`, and `errors`, with `result == data`.
- No live agent, real Prefect run, Docker, backend, frontend, Playwright,
  provider API, source state, or `/var/lib/grace-orchestrator/**` mutation was
  performed during automated review.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_live_opt_in_single_scratch_packet.py tests/test_prefect_grace_cli_live_opt_in_single_scratch_packet.py tests/test_prefect_grace_prefect_real_dry_run_seeded_smoke.py tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_cli_contracts.py`: `58 passed`.
- `pytest -q tests/test_prefect_grace_cli_command_module_split.py`: `5 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/live_opt_in_single_scratch_packet.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/cli.py`: passed.
- `python3 scripts/check_size_limits.py --root prefect_grace/platform --strict --max-file-lines 1000`: passed.
- Strict packet validation: `ok=true`, `warnings=0`, `errors=0`.
- Evidence manifest validation: `ok=true`, `warnings=[]`, `errors=[]`.
- CLI guard without opt-in exits `1`, returns `ok=false`,
  `opt_in_confirmed=false`, `agent_launch_count=0`, and no submission metadata.
- `sync-packets --dry-run --json`: `ok=true`, `registry_updates=0`.

## Post-Test Evidence

- Observability verdict: `degraded-but-expected`.
- Degradation is expected and bounded: the real live-agent smoke was not run
  without separate Architect approval and is recorded as
  `not_run_live_agent_not_approved`.
- Offline and injected evidence is clean for gate behavior, registry
  selection, scratch scope, and stable CLI envelopes.

This packet is ready for acceptance.
