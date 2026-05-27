# Review 0002 — FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP

**Verdict:** `rework_required`
**Reviewed by:** Codex reviewer
**Date:** 2026-05-26

## Summary

Attempt 0002 fixed the original scope blockers around `scripts/grace_lint.py`, missing test files, and frozen `backlog_controller.py` / `state_store.py` changes. The exact packet targeted tests and regression tests pass.

I amended the packet contract to include `tests/test_prefect_grace_backlog_controller_rework.py`, because the packet intentionally changes `submit-packets --execute` behavior and the old safety-gate assertion became obsolete. After that amendment, current tracked implementation scope is limited to allowed files and there are no frozen-scope violations.

## Verification Performed

Targeted packet tests:

```text
35 passed in 2.99s
```

Regression packet tests:

```text
36 passed in 2.98s
```

Static checks:

```text
compileall: PASS
scripts/grace_lint.py prefect_grace/platform/prefect_native_submission.py: PASS
scripts/grace_lint.py prefect_grace/platform/runtime_adapter.py: PASS
scripts/grace_lint.py prefect_grace/tasks/prefect_submitter.py: PASS
validate-packet --strict: PASS
```

Additional existing feature-submit compatibility test:

```text
tests/test_prefect_grace_prefect_submitter.py: 3 passed
```

Scope after cleanup:

```text
frozen_violations: none
outside_allowed_tracked: none
```

## Remaining Blocker

### BLOCKER-1 — `PrefectRuntimeAdapter.submit_packet_run` public API is broken

`prefect_grace/platform/runtime_adapter.py` still has the old `PrefectRuntimeAdapter.submit_packet_run()` implementation, but it now calls `submit_feature_flow_run()` with a stale signature:

```python
flow_run = submit_feature_flow_run(
    feature_id=feature_id,
    parameters=parameters,
    work_pool=self.work_pool,
    queue=self.queue,
)
```

The new `submit_feature_flow_run()` signature accepts only:

```python
submit_feature_flow_run(*, parameters, scheduled_for=None, tags=None, idempotency_key=None)
```

Observed minimal failure:

```text
TYPE_ERROR submit_feature_flow_run() got an unexpected keyword argument 'feature_id'
```

This breaks a public runtime adapter method in a file changed by this packet. Even if the new CLI path uses `FeatureSubmitter`/`ManagedPacketSubmitter`, the old adapter API must not be left in a broken state.

Required rework:

- Update `PrefectRuntimeAdapter.submit_packet_run()` to call the current `submit_feature_flow_run(parameters=..., tags=...)` API, or delegate to `FeatureSubmitter` correctly.
- Add/adjust a regression test that directly covers `PrefectRuntimeAdapter.submit_packet_run()` and fails before this fix.
- Re-run packet targeted tests, packet regression tests, `tests/test_prefect_grace_runtime_adapter.py`, and `tests/test_prefect_grace_prefect_submitter.py`.

## Notes

- `prefect_submitter.py` no longer imports Prefect directly; this part is correct.
- `scripts/grace_lint.py` is clean; this part is accepted.
- Managed packet submission uses `prefect-grace-managed-packet-runner/live-managed-packet-runner`, not the feature pipeline deployment; this part is accepted.
