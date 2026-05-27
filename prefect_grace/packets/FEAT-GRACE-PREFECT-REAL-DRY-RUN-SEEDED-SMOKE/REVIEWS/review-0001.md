# Review 0001 - FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE

status: accepted
reviewer: codex
source_hash: sha256:2076a915387ad3e63d3bae217245af88be890be5d9cfc269c4aca985dd420291
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

accepted

## What Passed

- The smoke builds a bounded synthetic packet corpus under the explicit
  `packet_root`, seeds a temporary registry from bounded terminal evidence, and
  derives exactly one runnable child from registry state.
- Accepted parent evidence is skipped for submission, while missing dependency,
  blocked dependency, source-status-only, and command `status: passed` fixtures
  remain unsubmitted.
- The dry submit planning layer creates zero Prefect runs and reports
  `packets_to_submit=["CHILD-RUNNABLE"]`.
- The live submission path is still constrained to the existing E2E runner
  deployment, with submitted parameters carrying `dry_run=true` and
  `execute_agent=false` in unit-injected verification.
- `--execute-agent` fails closed before submission with
  `PREFECT_SEEDED_DRY_RUN_EXECUTE_AGENT_REJECTED`.
- Root validation rejects broad or unsafe roots before destructive cleanup, and
  review spot checks confirmed `/tmp` is rejected as a root.
- The CLI JSON envelope preserves `ok`, `project_key`, `command`, `result`,
  `data`, `warnings`, and `errors`, with `result == data`.
- Product backend/frontend, Docker, Playwright, provider APIs, live agents,
  `prefect_grace/state/*.yaml`, and `/var/lib/grace-orchestrator/**` were not
  touched.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_real_dry_run_seeded_smoke.py tests/test_prefect_grace_cli_prefect_real_dry_run_seeded_smoke.py tests/test_prefect_grace_prefect_e2e_real_dry_run_smoke.py tests/test_prefect_grace_prefect_native_submission.py tests/test_prefect_grace_cli_contracts.py`: `50 passed`.
- `pytest -q tests/test_prefect_grace_cli_command_module_split.py`: `5 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/prefect_real_dry_run_seeded_smoke.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/cli.py`: passed.
- Strict packet validation: `ok=true`, `warnings=0`, `errors=0`.
- CLI help exposes the required seeded smoke flags.
- CLI `--execute-agent --json` returns `ok=false`, no submission metadata, and
  `code=PREFECT_SEEDED_DRY_RUN_EXECUTE_AGENT_REJECTED`.
- CLI broad-root spot check with `state_root=/tmp` returns `ok=false` and
  `code=UNSAFE_STATE_ROOT`.
- Real CLI no-wait smoke reaches the real submitter path, selects
  `CHILD-RUNNABLE`, creates `0` Prefect runs, starts `0` live agents, and fails
  closed with `SUBMISSION_FAILED: Prefect unavailable: No module named
  'prefect'`.

## Post-Test Evidence

- Observability verdict: `degraded-but-expected`.
- Degradation is expected and bounded: Prefect is not installed in this coder
  environment, so real Prefect verification is recorded as
  `not_run_prefect_unavailable` instead of being faked.
- Synthetic fixture warnings for `review-0001.md`, `SUMMARY.md`, and missing
  dependency cases are expected for this smoke corpus.

This packet is ready for acceptance.
