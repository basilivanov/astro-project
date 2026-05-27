# Review 0001 — FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP

status: rework_required
reviewer: codex
source_hash: sha256:760c9c28f6576401349adc7e85aa42394902acbd7c2fe7beda9d1ba358e58ec6
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

Rework required.

The implementation is structurally correct and the packet verification passes,
but the classifier is not fail-closed enough for the packet contract.

## Blocking Issue

### 1. Non-zero exit with no error text is classified as `none`

Observed directly:

```python
classify_agent_failure(stderr_text="", stdout_text="", exit_code=1)
```

Actual result:

```text
category == "none"
```

This contradicts the packet objective:

- failures such as provider/API errors must surface as typed runtime outcomes;
- unknown errors must be classified as `unknown_api_error`;
- downstream routing must not silently lose a failed agent exit.

If the process exits non-zero and no known failure pattern matches, the safe
default should be `unknown_api_error` rather than `none`.

## Additional Note

- The packet is otherwise narrow and the launcher metadata wiring is minimal.
- The current tests are green, but the green suite encodes the wrong behavior
  for this edge case.

## Required Fix

- Make non-zero exit codes fail closed into `unknown_api_error` when no more
  specific pattern matches.
- Preserve the current typed categories and launcher metadata wiring.
- Add or update a regression test for the empty-output non-zero exit case.

## Verification

- Targeted tests: `54 passed`
- Compileall: passed
- GRACE lint: passed
- Packet validation: passed

## Notes

- No live APIs were called.
- No retry/backoff policy was added.
- This packet is not ready for acceptance until the fail-closed edge case is
  corrected.
