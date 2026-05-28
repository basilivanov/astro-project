# Rework Summary: stale Prefect idempotency key

## Runtime Blocker
Reviewer live verification proved the payload retrieval path was not exercised because Prefect reused stale flow run `fd78bb2c-1dcf-44b1-8862-20fc0c481a47` from the pre-fix attempt. The synthetic live pilot used the same packet id and source hash on each run, so the existing idempotency key `project_key + packet_id + attempt + source_hash` could resolve to an old flow run without `managed_result_payload_path`.

## Fix
- Added optional `idempotency_namespace` to native packet submission idempotency plumbing.
- Kept default `build_idempotency_key()` output unchanged when no namespace is provided.
- Made `run_single_live_prefect_packet_pilot()` pass a bounded proof-run namespace derived from the fresh temp roots.
- Verified dry-run planned records and live submitter calls carry the namespaced proof-run idempotency key.
- Added regression coverage proving different temp roots produce different synthetic pilot idempotency keys.

## Runtime Scope
No real live Prefect pilot was run by worker-coder during this rework. The reviewer blocker was addressed with targeted unit/contract coverage only.
