# Review 0003 — FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP

**Verdict:** `rework_required`
**Reviewed by:** Codex reviewer
**Date:** 2026-05-26

## Summary

Attempt 0003 fixes the narrow blocker from review-0002: `PrefectRuntimeAdapter.submit_packet_run()` no longer calls `submit_feature_flow_run()` with the obsolete `feature_id=...` signature.

I amended the packet contract to include the new regression file:

- `tests/test_prefect_grace_runtime_adapter_submit_packet_run.py`

After cleanup, targeted tests, regression tests, compile, GRACE lint, and packet validation pass.

## Verification Performed

Updated targeted packet tests:

```text
39 passed in 3.13s
```

Regression / compatibility tests:

```text
48 passed in 2.81s
```

Static checks:

```text
compileall: PASS
scripts/grace_lint.py prefect_grace/platform/prefect_native_submission.py: PASS
scripts/grace_lint.py prefect_grace/platform/runtime_adapter.py: PASS
scripts/grace_lint.py prefect_grace/tasks/prefect_submitter.py: PASS
validate-packet --strict: PASS
```

Scope after cleanup:

```text
frozen_violations: none
```

## Remaining Blocker

### BLOCKER-1 — `PrefectRuntimeAdapter.submit_packet_run()` still breaks generic runtime parameters

The public `WorkflowRuntime.submit_packet_run(packet, parameters)` abstraction accepts a generic `parameters` dict. The new implementation forwards that dict into `feature_flow_parameters()` using `**parameters`:

```python
flow_params = feature_flow_parameters(
    feature_id=feature_id,
    **parameters,
)
```

That means any runtime parameter not accepted by `feature_flow_parameters()` raises `TypeError` before submission. Minimal repro:

```python
from prefect_grace.platform.runtime_adapter import PrefectRuntimeAdapter

PrefectRuntimeAdapter().submit_packet_run(
    {"packet_id": "P1", "feature_id": "F1"},
    {"x": 1},
)
```

Observed result:

```text
TypeError: feature_flow_parameters() got an unexpected keyword argument 'x'
```

This is still a public API regression: `DryRunRuntime.submit_packet_run()` preserves arbitrary runtime parameters, while `PrefectRuntimeAdapter.submit_packet_run()` now rejects them accidentally.

Required rework:

- Do not blindly unpack arbitrary `parameters` into `feature_flow_parameters()`.
- Either:
  - filter/normalize only known feature-flow fields and preserve unknown parameters under `business_context` or a safe metadata field; or
  - define and enforce a documented required parameter shape for `PrefectRuntimeAdapter.submit_packet_run()` and fail with a clear `ValueError`, not accidental `TypeError`.
- Add a regression test for arbitrary/unknown runtime parameters proving the adapter does not crash with `TypeError`.
- Add a regression test for missing `title`/`summary`, because `feature_flow_parameters()` requires both and `packet` may need to provide defaults.

Suggested minimal behavior:

```python
title = str(parameters.get("title") or packet.get("title") or packet_id)
summary = str(parameters.get("summary") or packet.get("summary") or "")
known_kwargs = { ... only keys accepted by feature_flow_parameters ... }
flow_params = feature_flow_parameters(feature_id=feature_id, title=title, summary=summary, **known_kwargs)
```

## Notes

- `prefect_submitter.py` separation from Prefect SDK imports remains accepted.
- Managed packet submission deployment selection remains accepted.
- The new `tests/test_prefect_grace_runtime_adapter_submit_packet_run.py` is the right place to add the missing regression cases.
