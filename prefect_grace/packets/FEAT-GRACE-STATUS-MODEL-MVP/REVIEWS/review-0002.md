# Review 0002 — FEAT-GRACE-STATUS-MODEL-MVP

status: rework_required
reviewer: codex
source_hash: sha256:5fc722553837d1a2b340a35a757f61460f0a1f6712196ab88c7ce71cf8d876a2
attempt: attempt-0001
reviewed_at: 2026-05-27

## Verdict

Rework required.

## What Passed

- `prefect_grace/platform/status_model.py` exists and is structurally coherent.
- Enums, normalization helpers, transition helper, and predicates are present.
- Unknown domain statuses fail closed to blocked/runner-error paths, not accepted.
- Targeted verification passes: `104 passed`.
- Compile, GRACE lint, and packet validation pass.
- Frozen scope is clean: `feature_pipeline.py` and `codex_launcher.py` are untouched.

## Blocking Issue

### 1. Focused integration required by the packet was not implemented

The packet explicitly requires narrow integration in:

- `backlog_controller.py`;
- `managed_packet_runner.py`;
- `worktree_scope_lifecycle.py`;
- `verifier_reviewer_handoff.py`;
- `executor_registry.py`;
- optionally `cli.py`.

Current diff only adds:

- `prefect_grace/platform/status_model.py`;
- `tests/test_prefect_grace_status_model.py`.

A direct search for `status_model`, `DomainStatus`, `RegistryStatus`, or `apply_domain_result_to_registry` in the allowed integration modules returns no usages. That means the platform still has the old string drift in runtime paths, and the packet objective is only partially satisfied.

## Required Fix

Keep the integration narrow. Do not rewrite state machines.

Minimum acceptable integration:

1. Use `DomainStatus` constants or `normalize_domain_status(...)` in `managed_packet_runner.py` for emitted `domain_status` values.
2. Use `RegistryStatus` constants or `normalize_registry_status(...)` in `backlog_controller.py` for registry status comparisons/writes in focused places.
3. Use `apply_domain_result_to_registry(...)` in at least one boundary where a domain execution result is converted to registry intent, or add a documented helper ready for `E2E` runner consumption with tests.
4. Update existing tests to prove public JSON still emits strings, not enum objects.
5. Preserve public status string values.

## Verification

Already passed in current attempt:

- Targeted tests: `104 passed in 2.78s`
- GRACE lint: passed
- Compileall: passed
- Packet validation: passed
- Frozen scope check: empty

## Notes

- Do not edit `feature_pipeline.py` or `codex_launcher.py`.
- Do not broaden this into a full migration.
- The status model module itself is acceptable; the blocker is missing runtime integration.
