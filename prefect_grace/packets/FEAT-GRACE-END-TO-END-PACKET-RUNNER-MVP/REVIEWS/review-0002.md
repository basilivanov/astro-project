# Review 0002 — FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP

status: rework_required
reviewer: codex
source_hash: sha256:2a9865d8e8a59b8cd6ed263bbc461e8f933e50aad7f135e46dc340d30f5ee13f
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

Rework required.

## Blocking Issues

### 1. Packet verification contract is not satisfied

The packet's own verification block requires these tests:

- `tests/test_prefect_grace_e2e_packet_runner.py`
- `tests/test_prefect_grace_e2e_packet_runner_flow.py`
- `tests/test_prefect_grace_e2e_packet_artifacts.py`
- `tests/test_prefect_grace_cli_e2e_packet_runner.py`
- `tests/test_prefect_grace_cli_contracts.py`

Current implementation only provides:

- `tests/test_prefect_grace_e2e_packet_runner.py`
- `tests/test_prefect_grace_cli_e2e_packet_runner.py`

The flow wrapper and artifact publication pieces declared by the packet are missing, so the packet does not yet meet its declared contract.

### 2. `rework_required` currently reports `ok=True`

The packet says successful end-to-end acceptance should be `ok=True`, and the CLI exit code should be `1` for `rework_required` / `blocked`.

Current behavior for the runner is inconsistent with that contract:

- `domain_status == "rework_required"`
- `ok == True`

This makes the runner report a non-accepted packet as successful.

## Evidence

- Targeted tests on available files: `33 passed, 1 skipped`
- Regression tests: `56 passed`
- `python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py`: passed
- `python3 scripts/grace_lint.py prefect_grace/platform/e2e_packet_runner.py`: passed
- `python3 -m prefect_grace.cli validate-packet ...`: passed
- Exact packet verification command fails because the declared flow/artifact test files are absent.

## Required Fix

- Add the missing flow/artifact pieces or remove them from the packet contract and verification block.
- Make `ok` false for `rework_required` / `blocked` / `scope_blocked` / `agent_failed` / `runner_error` / `handoff_error`.
- Keep dry-run default and keep live agent execution out of the default path.

## Notes

- No product backend/frontend files were modified.
- No live agents were launched.
- No merge/push/squash/delete-worktree operation happened.
