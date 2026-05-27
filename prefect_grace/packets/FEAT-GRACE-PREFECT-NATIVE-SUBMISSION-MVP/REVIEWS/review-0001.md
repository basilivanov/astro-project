# Review 0001 — FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP

**Verdict:** `rework_required`
**Reviewed by:** Codex reviewer
**Date:** 2026-05-26

## Summary

Implementation is not acceptable yet. The main functionality may be close, but the packet currently violates its own frozen scope and does not pass the exact verification command declared in `EXECUTION_PACKET.md`.

## Blockers

### BLOCKER-1 — Frozen scope modified

The execution packet freezes these files, but the implementation changed them:

- `scripts/grace_lint.py`
- `prefect_grace/platform/backlog_controller.py`
- `prefect_grace/platform/state_store.py`

This directly violates packet scope. The packet also explicitly requires evidence that `scripts/grace_lint.py` has no diff, but the submitted evidence contains `grace_lint_diff.txt` and describes a linter change.

Required rework:

- Revert `scripts/grace_lint.py`.
- Revert `prefect_grace/platform/backlog_controller.py` and `prefect_grace/platform/state_store.py`, or stop and escalate with a separate packet/scope amendment.
- Make `prefect_submitter.py` pass current lint without changing lint rules. If the current lint incorrectly flags lazy imports, the correct fix is local module structure/import placement, not linter widening in this packet.

### BLOCKER-2 — Exact packet verification command fails

The targeted command from the packet fails immediately:

```text
pytest -q \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_prefect_submitter_managed_packet.py \
  tests/test_prefect_grace_runtime_adapter_prefect_submission.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_cli_contracts.py
```

Observed result:

```text
ERROR: file or directory not found: tests/test_prefect_grace_prefect_submitter_managed_packet.py
no tests ran
```

Required rework:

- Create/use the exact test files named by the packet, or update the packet before implementation and get it re-approved.
- Do not substitute with `tests/test_prefect_grace_cli_submit_packets.py` without packet approval.

### BLOCKER-3 — Evidence contradicts scope compliance

`EVIDENCE/attempt-0001/git_diff_name_only.txt` lists files outside allowed scope, including frozen files, but `evidence_manifest.json` claims:

```json
"allowed_write_scope_only": true
```

Required rework:

- Regenerate evidence after scope cleanup.
- Evidence must truthfully report outside-scope files and frozen-scope violations.

### BLOCKER-4 — Untracked implementation files are outside declared test names

Current untracked files include:

- `prefect_grace/platform/prefect_native_submission.py`
- `tests/test_prefect_grace_prefect_native_submission.py`
- `tests/test_prefect_grace_cli_submit_packets.py`

The first two are in scope. `tests/test_prefect_grace_cli_submit_packets.py` is not the declared test path for this packet.

Required rework:

- Rename/split the CLI tests to `tests/test_prefect_grace_cli_submit_packets_prefect_native.py`, or amend packet scope before implementation.

## Non-blocking note

`prefect_grace/tasks/prefect_submitter.py`, `prefect_grace/platform/runtime_adapter.py`, `prefect_grace/platform/prefect_native_submission.py`, and `prefect_grace/cli.py` are the right implementation areas for this packet. Keep the rework focused there.

## Required Verification After Rework

Run the exact commands from `EXECUTION_PACKET.md`, not a substituted set:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_prefect_submitter_managed_packet.py \
  tests/test_prefect_grace_runtime_adapter_prefect_submission.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_cli_contracts.py

pytest -q \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_backlog_controller_rework.py \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_cli_worktree_scope_flow.py

python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/prefect_native_submission.py
python3 scripts/grace_lint.py prefect_grace/platform/runtime_adapter.py
python3 scripts/grace_lint.py prefect_grace/tasks/prefect_submitter.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Also provide:

```bash
git diff --name-only
```

It must be limited to allowed scope plus this packet's artifact directory.
