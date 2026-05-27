# Review 0002

**Verdict:** `rework_required`
**Timestamp:** `2026-05-26T11:27:41.710881+00:00`

## Metadata

- **reviewer:** `codex-reviewer`

## Review Body

# Reviewer Verdict: REWORK_REQUIRED

## Findings

1. BLOCKER: Runtime resume gate is still not enforced on the execution path. Attempt 0002 stores resume state in registry and updates it during backlog sync, but `prefect_grace/flows/feature_pipeline.py` and `prefect_grace/tasks/codex_launcher.py` still do not read `resume_allowed`, `resume_block_reason`, `recommended_rework_mode`, `last_executed_source_hash`, or `latest_coder_session_id` before launching/resuming coder work. Result: live pipeline can still choose `light_resume` through existing `execution_hints.resume_strategy=packet_parent` and Codex launcher can still resume an old thread without consulting the source-hash decision.

2. MAJOR: The registry integration is passive. `BacklogController.sync()` marks changed accepted/blocked packets as `resume_allowed=False`, but no subsequent submit/run path is required to consume that registry decision. This improves observability but does not yet make stale resume impossible.

3. MAJOR: `last_executed_source_hash` and `latest_coder_session_id` are stored by `PacketRegistryStore.update_resume_state(...)`, but no execution-start hook writes them when a coder attempt actually starts. Without that write, future comparisons can be missing or stale.

## Resolved Since Review 0001

- `missing_session` handling exists in `decide_rework_resume(...)` via `latest_coder_session_id`.
- `fresh_context_requested` was replaced by contract-approved `decision_required`.
- `--session-id` was added to CLI and same-hash + session allows `light_resume`.
- Registry can preserve and update resume fields without breaking old records.

## Verification Run By Reviewer

- `pytest -q tests/test_prefect_grace_rework_resume_policy.py tests/test_prefect_grace_state_store_resume.py tests/test_prefect_grace_backlog_controller.py tests/test_prefect_grace_backlog_controller_rework.py tests/test_prefect_grace_backlog_controller_resume_integration.py` -> 33 passed.
- `pytest -q tests/test_prefect_grace_packet_artifact_layout.py tests/test_prefect_grace_context_bundle.py` -> 21 passed.
- `pytest -q tests/test_prefect_grace_codex_launcher.py tests/test_prefect_grace_feature_pipeline_dynamic.py` -> 48 passed.
- `python3 -m compileall prefect_grace` -> passed, but output is very large because it traverses ignored state/run artifacts.
- `python3 scripts/grace_lint.py prefect_grace/platform/state_store.py prefect_grace/platform/backlog_controller.py prefect_grace/platform/rework_resume_policy.py` -> passed.
- `python3 -m prefect_grace.cli validate-packet ... --strict --json` -> ok, warnings=[], errors=[].
- CLI same hash without `--session-id` -> `resume_allowed=false`, `resume_block_reason=missing_session`.
- CLI same hash with `--session-id session-123` -> `resume_allowed=true`, `recommended_rework_mode=light_resume`.

## Required Rework

1. Wire `decide_rework_resume(...)` or persisted registry decision into `feature_pipeline` before constructing light-resume rework packets.
2. Wire the decision into `codex_launcher` so `resume_allowed=False` always forces fresh `codex exec` and never passes an old thread id.
3. Persist `last_executed_source_hash` and `latest_coder_session_id` at coder attempt start/success in the registry.
4. Add tests proving changed source hash prevents `packet_parent` resume in feature pipeline and proving launcher drops old session/thread id when resume is blocked.

## Status

Attempt 0002 is a useful partial rework, but the packet remains blocked until Task #31 completes runtime enforcement.

