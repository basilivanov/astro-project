# Review 0001: FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY

## Verdict

accepted

## Findings

No blocking findings.

## Scope Review

- Reviewed `prefect_grace/platform/nightly_dry_run_controller.py`.
- Reviewed `prefect_grace/platform/runtime_lock.py`.
- Reviewed CLI wiring in `prefect_grace/cli_commands/prefect_smokes.py` and `prefect_grace/cli_commands/parser.py`.
- Reviewed targeted tests and bounded evidence under `EVIDENCE/attempt-0001/`.

## Reviewer Notes

- `run-nightly` now returns a deterministic dry-run plan instead of the old contract-only placeholder.
- `--execute` fails closed with `NIGHTLY_EXECUTION_NOT_ENABLED` and zero live side effects.
- Dry-run planning uses bootstrap, sync, and submit planning contracts; it does not create Prefect runs or start agents.
- Runtime lock behavior is covered for acquired/released, already-running, stale replacement, cleanup on failure, and real-project ephemeral lock reporting.
- Reviewer tightened the runtime summary so accepted source/runtime mismatch IDs are bounded with a total count.
- Reviewer corrected evidence artifact paths so `validate-evidence-manifest` can validate artifacts with `/opt/astro-project` as artifact root.

## Verification

- `pytest -q tests/test_prefect_grace_nightly_dry_run_controller.py tests/test_prefect_grace_cli_nightly_dry_run.py tests/test_prefect_grace_backlog_controller.py tests/test_prefect_grace_controller_backlog_bootstrap.py tests/test_prefect_grace_cli_contracts.py` -> 51 passed
- `pytest -q tests/test_prefect_grace_registry_apply_smoke.py tests/test_prefect_grace_registry_bootstrap_apply.py tests/test_prefect_grace_cli_submit_packets_prefect_native.py` -> 18 passed
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py prefect_grace/cli_commands` -> pass
- `python3 scripts/grace_lint.py prefect_grace/platform/nightly_dry_run_controller.py` -> pass
- `python3 scripts/grace_lint.py prefect_grace/platform/runtime_lock.py` -> pass
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/prefect_smokes.py` -> pass
- `python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py` -> pass
- `python3 scripts/grace_lint.py prefect_grace/cli.py` -> pass
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER/EXECUTION_PACKET.md --strict --json` -> ok=true
- `python3 -m prefect_grace.cli validate-evidence-manifest ... --artifact-root /opt/astro-project --json` -> ok=true with non-blocking unknown-evidence-id warnings
- `python3 -m prefect_grace.cli run-nightly --project prefect_grace/project.yaml --dry-run --until-blocked --json` -> ok=true, preflight_status=blocked, stop_reason=source_runtime_mismatch, prefect_runs_created=0, live_agents_started=0, lock released
- `python3 -m prefect_grace.cli run-nightly --project prefect_grace/project.yaml --until-blocked --execute --json` -> ok=false, NIGHTLY_EXECUTION_NOT_ENABLED, prefect_runs_created=0, live_agents_started=0

## Observability Verdict

degraded-but-expected

The real project runtime root is not writable in this environment, so the
real-project dry-run reports `lock_ephemeral=true`. No live Prefect
submissions, live agents, worktrees, registry mutations, Docker, backend,
frontend, Playwright, provider APIs, credentials, commits, merges, or pushes
were used.
