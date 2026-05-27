# Review 0002 — FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP

status: rework_required
reviewer: codex
source_hash: sha256:760c9c28f6576401349adc7e85aa42394902acbd7c2fe7beda9d1ba358e58ec6
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

Rework required.

## Blocking Issue

### 1. Non-zero exit with no error text is still classified as `none`

Direct check remains fail-open for the key edge case:

```python
classify_agent_failure(stderr_text="", stdout_text="", exit_code=1)
```

Actual result:

```text
category == "none"
```

That is incompatible with the packet objective. A non-zero agent/provider exit with no recognized pattern must fail closed into `unknown_api_error`.

## Why this matters

The classifier is supposed to distinguish infrastructure/provider blockers from quality rework. Returning `none` on a failed exit hides a failed provider/agent run and prevents downstream routing from seeing a typed failure outcome.

## Required Fix

- Treat `exit_code != 0` with no recognized pattern as `unknown_api_error`.
- Preserve the current typed metadata flow into `codex_launcher.py`.
- Add or update a regression test for the empty-output non-zero exit case.

## Verification

- Targeted tests: `54 passed`
- Compileall: passed
- GRACE lint: passed
- Packet validation: passed

## Notes

- No live APIs were called.
- No retry/backoff policy was added.
- The packet is not ready for acceptance until the fail-closed edge case is corrected.
