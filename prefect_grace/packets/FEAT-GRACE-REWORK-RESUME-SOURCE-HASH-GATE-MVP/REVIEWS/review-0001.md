# Review 0001

**Verdict:** `rework_required`
**Timestamp:** `2026-05-26T10:58:58.217688+00:00`

## Metadata

- **reviewer:** `codex-reviewer`

## Review Body

# Reviewer Verdict: REWORK_REQUIRED

## Findings

1. BLOCKER: Runtime gate is not wired into the orchestrator. The packet requires registry writes for `last_executed_source_hash`, `latest_coder_session_id`, `resume_allowed`, `resume_block_reason`, and `recommended_rework_mode`, and also requires the launcher to receive an explicit resume decision. The implementation only adds the pure policy and CLI. `rg` shows no new integration in `prefect_grace/platform/state_store.py`, `prefect_grace/flows/feature_pipeline.py`, or `prefect_grace/tasks/codex_launcher.py`. Result: live Prefect/Codex execution can still resume stale coder sessions because the gate is not on the execution path.

2. BLOCKER: Missing/stale session safety is not implementable with the current policy signature. The packet requires stale or missing session to forbid resume, but `decide_rework_resume(...)` has no session id/state input. For same hash plus reviewer feedback it returns `resume_allowed=True` and `context_paths=[]` unconditionally. Result: the policy can approve resume even when there is no usable coder session to resume.

3. MAJOR: `resume_block_reason="fresh_context_requested"` is emitted but is not part of the packet's accepted reason enum. Accepted values are `contract_changed`, `missing_last_executed_hash`, `missing_session`, `stale_session`, `attempt_policy_exceeded`, and `decision_required`. Result: downstream routing or dashboard logic relying on stable reason values may break.

4. MAJOR: CLI cannot exercise missing last executed hash because `--last-executed-source-hash` is required. The pure function covers `None`, but operator/automation CLI cannot represent the packet's missing-hash scenario without adding a sentinel outside the contract.

5. MINOR: `resolve_packet_layout(...)` is assigned to unused local variables in three branches. `compileall` passes, but a Ruff/Pyflakes style gate would likely flag these assignments. Ruff is not installed in the current shell, so this could not be verified locally.

## Verification Run By Reviewer

- `pytest -q tests/test_prefect_grace_rework_resume_policy.py tests/test_prefect_grace_context_bundle.py tests/test_prefect_grace_yaml_state.py tests/test_prefect_grace_cli_contracts.py` -> 21 passed.
- `pytest -q tests/test_prefect_grace_project_adapter.py tests/test_prefect_grace_packet_parser.py tests/test_prefect_grace_scope_guard.py tests/test_prefect_grace_yaml_state.py tests/test_prefect_grace_cli_contracts.py tests/test_prefect_grace_dag.py tests/test_prefect_grace_backlog_controller.py tests/test_prefect_grace_backlog_controller_rework.py tests/test_prefect_grace_runtime_adapter.py tests/test_prefect_grace_packet_artifact_layout.py` -> 70 passed.
- `pytest -q tests/test_prefect_grace_codex_launcher.py tests/test_prefect_grace_feature_pipeline_dynamic.py` -> 48 passed.
- `python3 -m compileall prefect_grace/platform/rework_resume_policy.py prefect_grace/cli.py` -> passed.
- `python3 scripts/grace_lint.py prefect_grace/platform/rework_resume_policy.py` -> passed.
- `python3 -m prefect_grace.cli validate-packet ... --strict --json` -> ok, warnings=[], errors=[].
- CLI smoke changed hash -> `resume_allowed=false`, `resume_block_reason=contract_changed`.
- CLI smoke same hash -> `resume_allowed=true`, `recommended_rework_mode=light_resume`.
- Ruff check not run: `ruff` and `python3 -m ruff` are unavailable in this environment.

## Required Rework

1. Wire the policy into the runtime path before coder launch/rework routing, not only into CLI.
2. Persist and read `last_executed_source_hash`, `latest_coder_session_id`, resume decision fields, and attempt state from registry/state store.
3. Add session-state input or lookup so missing/stale sessions force `bounded_fresh`.
4. Replace `fresh_context_requested` with a contract-approved reason or update the packet contract before implementation.
5. Add regression tests proving `codex_launcher` never receives old session id when `resume_allowed=false` and proving feature pipeline routes changed contract to bounded fresh.

