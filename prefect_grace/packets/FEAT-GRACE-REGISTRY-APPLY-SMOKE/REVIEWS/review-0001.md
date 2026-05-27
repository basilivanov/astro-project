# Review 0001 — FEAT-GRACE-REGISTRY-APPLY-SMOKE

status: accepted
reviewer: codex
source_hash: sha256:a1796524b1b7adf9ae74797d17582f1e80d3ebbea36b538124ad007d5e8185b2
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

accepted

## What Passed

- The smoke uses an explicit temporary `state_root` and rejects
  `/var/lib/grace-orchestrator/**`.
- `packet_root` is rejected when it is outside the explicit `state_root`.
- Synthetic packet fixtures are written under the temporary smoke root, while
  the real source packet corpus is only used as the project config source.
- `bootstrap-backlog` is executed in apply mode against the temporary runtime
  registry only.
- `sync-packets` is exercised as a dry-run and the registry snapshot remains
  unchanged.
- `submit-packets` dry-run creates zero Prefect runs.
- Execute mode remains fail-closed with `NO_SUBMITTER_PROVIDED`.
- Accepted parent packets are not re-submitted, accepted dependencies make a
  dependent runnable, and missing/blocked dependencies do not become accepted.
- Source `status: accepted` and command-local `status: passed` do not seed
  registry `accepted`.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_registry_apply_smoke.py tests/test_prefect_grace_backlog_controller.py tests/test_prefect_grace_cli_contracts.py`: `34 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/registry_apply_smoke.py`: passed.
- Strict packet validation: `ok=true`, warnings `0`, errors `0`.
- `registry-apply-smoke --json` reviewer smoke: `ok=true`,
  `bootstrap_apply_count=7`, `prefect_runs_created=0`,
  `writes_outside_state_root=[]`, cases `10/10`, errors `0`.
- Unsafe `/var/lib/grace-orchestrator/**` state root returns
  `UNSAFE_STATE_ROOT`.
- `packet_root` outside `state_root` returns `UNSAFE_PACKET_ROOT`.

## Notes

- Post-test observability verdict is `degraded-but-expected`: fixture-local
  warnings for `SUMMARY.md`, `review-0001.md`, and missing dependency planning
  are expected for this synthetic smoke.
- `python3 scripts/grace_lint.py prefect_grace/cli.py` still fails on existing
  CLI-wide GRACE contract debt and unrelated local E2E smoke hunks. The scoped
  registry smoke command itself does not add a public uncontracted function.
- `writes_outside_state_root` is a smoke result field, not a complete filesystem
  write detector. The safety guarantee for this packet comes from explicit
  `state_root`/`packet_root` validation and project adapter overrides.
- Local notify/telegram changes are outside this packet's `files_changed`
  evidence and must not be bundled into the registry apply smoke packet commit.

This packet is ready for acceptance.
