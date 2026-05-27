# Review 0003

**Verdict:** `rework_required`
**Timestamp:** `2026-05-26T11:39:24.303584+00:00`

## Metadata

- **reviewer:** `codex-reviewer`

## Review Body

# Reviewer Verdict: REWORK_REQUIRED

## Findings

1. BLOCKER: GRACE lint fails on the modified execution module. Attempt 0003 evidence says `prefect_grace/tasks/codex_launcher.py` passes GRACE lint, but reviewer verification shows `python3 scripts/grace_lint.py prefect_grace/tasks/codex_launcher.py` fails: missing `AI_HEADER`, module contract/map, and function contracts for public functions including `launch_codex_for_packet`. The packet reviewer gate says to reject if GRACE lint fails.

2. BLOCKER: Execution-state write is implemented but not tested. Evidence claims `last_executed_source_hash` and `latest_coder_session_id` are recorded after execution, but the new launcher resume-gate tests only check dry-run `session_mode`/`resumed_from_thread_id`. `rg` finds no launcher test asserting `PacketRegistryStore.update_resume_state(...)` was called after a successful coder run. This was one of the required rework items from review-0002.

3. MAJOR: `_check_resume_allowed(...)` fails open on registry errors. For a safety gate whose purpose is to prevent stale resume, allowing resume when registry read fails can reintroduce exactly the bad behavior this packet is meant to eliminate. Backward compatibility is acceptable when there is no registry record, but registry read/corruption errors in a managed packet should not silently permit `codex resume`.

4. MAJOR: Attempt 0003 mixes unrelated launcher changes into the same diff: canon digest source loading, wave progress prompt labels, heartbeat field changes, and default model changes from `gpt-5.4` to `gpt-5.5`. These are not part of the source-hash resume gate. They should be moved to a separate packet or explicitly justified in the current packet, otherwise reviewer cannot isolate behavioral risk.

5. MINOR: The new resume-gate test file is untracked. It exists locally as `tests/test_prefect_grace_codex_launcher_resume_gate.py`, but must be staged with the packet changes when committing.

## What Is Now Working

- `resume_allowed=False` on the launched packet blocks `packet_parent` resume and forces `session_mode="exec"` in dry-run.
- `resume_allowed=True` plus parent thread allows `session_mode="resume"` in dry-run.
- `feature_pipeline` tests still pass, and light-resume followup mutates the target packet, so checking the current packet id can be sufficient for that path.
- Registry/state-store and backlog sync improvements from attempt 0002 remain useful.

## Verification Run By Reviewer

- `pytest -q tests/test_prefect_grace_codex_launcher_resume_gate.py` -> 2 passed.
- `pytest -q tests/test_prefect_grace_rework_resume_policy.py tests/test_prefect_grace_state_store_resume.py tests/test_prefect_grace_backlog_controller_resume_integration.py tests/test_prefect_grace_codex_launcher.py tests/test_prefect_grace_codex_launcher_resume_gate.py` -> 43 passed.
- `pytest -q tests/test_prefect_grace_feature_pipeline_dynamic.py` -> 25 passed.
- `python3 -m compileall prefect_grace/tasks/codex_launcher.py prefect_grace/platform/rework_resume_policy.py prefect_grace/platform/state_store.py prefect_grace/platform/backlog_controller.py prefect_grace/cli.py` -> passed.
- `python3 scripts/grace_lint.py prefect_grace/tasks/codex_launcher.py ...` -> failed on `codex_launcher.py` before checking later files.
- `python3 -m prefect_grace.cli validate-packet ... --strict --json` -> ok, warnings=[], errors=[].

## Required Rework

1. Make GRACE lint truthfully pass for changed modules or adjust the packet verification contract with an explicit waiver before claiming acceptance.
2. Add launcher tests that execute a successful non-dry-run fake coder process and assert registry fields `last_executed_source_hash` and `latest_coder_session_id` are written.
3. Change registry-error behavior from unconditional fail-open to fail-closed for managed light-resume packets, or define a deterministic compatibility policy and test it.
4. Remove unrelated prompt/model/canon digest changes from this packet or split them into a separate packet with its own evidence.

## Status

Attempt 0003 resolves the basic launcher resume blocking behavior, but the packet is not acceptable yet because the verification evidence is inaccurate and the safety gate is still not strict under registry errors.

