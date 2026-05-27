# Review 0001 — FEAT-GRACE-CLI-COMMAND-MODULE-SPLIT

status: accepted
reviewer: codex
source_hash: sha256:0051515021fba7d381b81ed5a9ec95b37ef5f380ae778a18c31331ae5b2fd7d3
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

accepted

## What Passed

- `prefect_grace/cli.py` is now a small facade and remains the
  `python3 -m prefect_grace.cli` entrypoint.
- Command handlers and parser construction are extracted into
  `prefect_grace/cli_commands/*` modules grouped by command family.
- All 44 pre-split top-level commands remain registered.
- Compatibility imports from `prefect_grace.cli` are preserved for moved
  `_cmd_*` functions, shared helpers, `build_parser()`, and `main()`.
- Safety-sensitive flags remain covered for `submit-packets`, live smoke
  commands, queue/dashboard legacy commands, and JSON-envelope commands.
- `submit-packets --dry-run --json` creates zero submissions.
- File size and function token gates pass for the facade and every new command
  module.
- `prefect_grace/cli.py` and `prefect_grace/cli_commands` pass GRACE lint.

## Reviewer Fixups

- Restored legacy `queue` and `dashboard` handlers, parser registration, and
  facade re-exports. They were present in the old CLI and are required by the
  no-drift parser contract.
- Added `tests/test_prefect_grace_cli_command_module_split.py`, which was
  required by the packet but absent from the initial handoff. The test now
  records parser inventory, facade exports, and safety-sensitive flags.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_cli_command_module_split.py tests/test_prefect_grace_cli_contracts.py tests/test_prefect_grace_cli_submit_packets_prefect_native.py tests/test_prefect_grace_cli_prefect_e2e_real_dry_run_smoke.py tests/test_prefect_grace_cli_prefect_e2e_batch_smoke.py tests/test_prefect_grace_cli_prefect_e2e_live_smoke.py tests/test_prefect_grace_cli_e2e_packet_runner.py tests/test_prefect_grace_cli_e2e_packet_flow.py tests/test_prefect_grace_cli_handoff.py tests/test_prefect_grace_cli_managed_packet_runner.py tests/test_prefect_grace_cli_worktree_manager.py tests/test_prefect_grace_cli_worktree_scope_flow.py tests/test_prefect_grace_cli_worktree_scope_lifecycle.py tests/test_prefect_grace_cli_scope_guard.py`: `102 passed`.
- `python3 -m compileall -q prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- `python3 scripts/grace_lint.py prefect_grace/cli.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/cli_commands`: passed.
- `python3 scripts/check_size_limits.py --root prefect_grace/cli.py --strict --max-file-lines 1000 --max-function-tokens 4000`: passed.
- `python3 scripts/check_size_limits.py --root prefect_grace/cli_commands --strict --max-file-lines 1000 --max-function-tokens 4000`: passed.
- Strict packet validation: `ok=true`, `warnings=0`, `errors=0`.
- `validate-project --json`: `ok=true`, `result == data`.
- `submit-packets --dry-run --json`: `ok=true`, `packets_submitted=[]`.

## Post-Test Evidence

- Observability verdict: `clean`.
- Reviewed `logs/gracectl/evidence-review-today-week.log`; latest verdict is
  `PASS_CLEAN`.
- No live agents, live Prefect submissions, Docker, backend, frontend,
  Playwright, provider APIs, `prefect_grace/state`, or
  `/var/lib/grace-orchestrator` writes were started by this review.

This packet is ready for acceptance.
