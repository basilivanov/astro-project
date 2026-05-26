# Independent Reviewer Recheck

verdict: REWORK_REQUIRED
reviewer: codex

## Accepted Improvements

- `sync-packets --dry-run` does not create Prefect runs.
- Empty `packet_id` entries are gone from real project sync output.
- `submit-packets --execute --json` fails closed with `SAFETY_GATE_NOT_READY` and exit code 5.
- New targeted tests pass.
- Nearby Prefect/GRACE regression tests pass.

## Blocking Issues

1. GRACE lint fails because `prefect_grace/platform/backlog_controller.py::update_dependent_packets` is public and lacks a `START_FUNCTION_CONTRACT`.
2. Backlog discovery still treats loose legacy role packet files as runnable packets.
3. Real repo audit found 757 files with ids, 3 strict controller packets, and 754 loose-but-not-strict files currently included by sync.
4. Rework tests cover empty metadata evidence docs, but not legacy role docs that contain ids while failing strict controller schema.

## Required Rework

- Add GRACE function contract for `update_dependent_packets` or make it private.
- Accept only strict controller packets by default in source backlog discovery.
- Skip/report historical role packets with ids but missing controller sections.
- Add regression test for loose-id legacy files.
- Re-run strict validation, targeted tests, compile, GRACE lint, and CLI smoke.

## Verification Performed

```text
Target tests: 54 passed in 1.40s
Nearby regression: 34 passed in 42.44s
Compile: pass
GRACE lint: failed
CLI sync: ok but includes 754 loose legacy files
CLI submit execute: fails closed with SAFETY_GATE_NOT_READY, exit 5
```
