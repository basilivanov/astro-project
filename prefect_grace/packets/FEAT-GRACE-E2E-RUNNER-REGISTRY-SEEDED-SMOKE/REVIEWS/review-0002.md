# Review 0002 — FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE

status: accepted
reviewer: codex
source_hash: sha256:6cc10e3ca7c7f929936c2604f3b46dafa3510035267a48d8645d286dc24abfb2
attempt: attempt-0002
reviewed_at: 2026-05-27

## Verdict

accepted

## What Passed

- The `review-0001` blocker is fixed. Root validation now requires
  `state_root`, `worktree_root`, and `packet_root` to be dedicated child
  directories under the system temp root, outside the repository and real GRACE
  runtime state, before destructive cleanup can run.
- Broad roots fail closed: `state_root=/opt/astro-project`, `state_root=/tmp`,
  `worktree_root=/tmp`, and `packet_root=/tmp` all return structured unsafe-root
  errors before `_reset_temp_runtime_roots()` is reached.
- Overlapping temp roots are rejected with `OVERLAPPING_TEMP_ROOTS`.
- The smoke still selects exactly `SMOKE-CHILD-RUNNABLE-W01-PACKET`, keeps
  accepted parents out of E2E selection, leaves missing/blocked dependencies
  unselected, and does not accept source `status: accepted` without bounded
  terminal evidence.
- The dry-run E2E runner path remains offline: zero Prefect runs and zero live
  agents.

## Regression Coverage Reviewed

- `tests/test_prefect_grace_e2e_runner_registry_seeded_smoke.py` covers the
  accepted registry-seeded flow, unsafe real GRACE state, repo-root state,
  broad `/tmp` roots, overlapping roots, and sentinel preservation under `/tmp`.
- `tests/test_prefect_grace_cli_e2e_runner_registry_seeded_smoke.py` covers CLI
  help shape, JSON envelope stability, and unsafe state-root rejection.
- `tests/test_prefect_grace_cli_contracts.py` verifies the new command exposes
  only the offline smoke flags and no live-agent execution toggles.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_e2e_runner_registry_seeded_smoke.py tests/test_prefect_grace_cli_e2e_runner_registry_seeded_smoke.py tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_cli_e2e_packet_runner.py tests/test_prefect_grace_cli_contracts.py`: `54 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/e2e_runner_registry_seeded_smoke.py`: passed.
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-REGISTRY-SEEDED-SMOKE/EXECUTION_PACKET.md --strict --json`: `ok=true`, `warnings=0`, `errors=0`.
- `python3 -m prefect_grace.cli run-e2e-registry-seeded-smoke --json`: `ok=true`,
  `selected_packet_id=SMOKE-CHILD-RUNNABLE-W01-PACKET`,
  `bootstrap_apply_count=6`,
  `prefect_runs_created=0`,
  `live_agents_started=0`,
  `writes_outside_temp_roots=[]`,
  `errors=0`.

## Notes

- This review supersedes `review-0001`; latest review evidence should mark this
  packet accepted.
- Post-test observability verdict is `degraded-but-expected`: the smoke emits
  expected synthetic fixture warnings for review/SUMMARY and missing-dependency
  cases, with no unexpected errors or live-runtime activity.
- The repo-wide `prefect_grace/cli.py` GRACE lint debt is pre-existing; the
  changed smoke module passes targeted lint and the CLI contract tests cover the
  new command shape.

This packet is ready for acceptance.
