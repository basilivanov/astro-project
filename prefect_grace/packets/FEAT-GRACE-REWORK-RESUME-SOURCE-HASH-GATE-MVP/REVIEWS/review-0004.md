# Review 0004

**Verdict:** `rework_required`
**Timestamp:** `2026-05-26T12:02:13.169032+00:00`

## Metadata

- **reviewer:** `codex-reviewer`

## Review Body

# Reviewer Verdict: REWORK_REQUIRED

## Findings

1. BLOCKER: Registry errors still fail open and allow resume. `_check_resume_allowed(...)` returns `True` on any exception from `PacketRegistryStore`, logging "Allowing resume." For a managed light-resume packet, registry read/corruption error must not silently permit `codex resume`, because this reintroduces the stale-resume failure mode the packet is designed to prevent. Missing registry record can remain backward-compatible, but registry errors for packets with resume strategy `feature_role` or `packet_parent` should fail closed or force `bounded_fresh`.

2. MAJOR: The packet still contains unrelated `codex_launcher.py` changes outside the source-hash resume gate: canon digest source loading, wave progress prompt labels, heartbeat turn-completed tracking, and default model changes from `gpt-5.4` to `gpt-5.5`. These changes increase behavioral risk and are not justified by the packet scope. They must be split into separate packets or reverted from this one.

3. MINOR: The new test file is staged, but several required files remain unstaged/untracked in `git status`. Before final acceptance/commit, all packet-owned code, tests, and ignored packet artifacts need deliberate staging, using `git add -f` for `prefect_grace/packets/**`.

## Resolved Since Review 0003

- GRACE lint now passes for `prefect_grace/tasks/codex_launcher.py`.
- `test_launch_codex_records_execution_state_after_coder_success` proves `last_executed_source_hash` and `latest_coder_session_id` are written after successful coder execution.
- Resume-gate tests now cover blocked resume, allowed resume, and execution-state recording.

## Verification Run By Reviewer

- `pytest -q tests/test_prefect_grace_codex_launcher_resume_gate.py tests/test_prefect_grace_rework_resume_policy.py tests/test_prefect_grace_state_store_resume.py tests/test_prefect_grace_backlog_controller_resume_integration.py tests/test_prefect_grace_codex_launcher.py` -> 44 passed.
- `pytest -q tests/test_prefect_grace_feature_pipeline_dynamic.py` -> 25 passed.
- `python3 scripts/grace_lint.py prefect_grace/tasks/codex_launcher.py` -> passed.
- `python3 -m compileall prefect_grace/tasks/codex_launcher.py prefect_grace/platform/rework_resume_policy.py prefect_grace/platform/state_store.py prefect_grace/platform/backlog_controller.py prefect_grace/cli.py` -> passed.
- `python3 -m prefect_grace.cli validate-packet ... --strict --json` -> ok, warnings=[], errors=[].

## Required Rework

1. Change `_check_resume_allowed(...)` so registry read errors fail closed for managed resume strategies, or pass enough context to distinguish legacy packets from managed light-resume packets. Add a test that simulates registry failure and asserts no `resume` command is used.
2. Remove unrelated `codex_launcher.py` changes from this packet or move them into a separate packet with its own contract and evidence.
3. Update evidence after rework with exact commands and diff scope.

## Status

Attempt 0004 closes the previous lint and execution-state blockers, but the safety gate cannot be accepted while registry errors allow resume and unrelated launcher changes remain in scope.

