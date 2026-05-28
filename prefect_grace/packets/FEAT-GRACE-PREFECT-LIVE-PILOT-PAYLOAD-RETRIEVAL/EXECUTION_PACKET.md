# Execution Packet: FEAT-GRACE-PREFECT-LIVE-PILOT-PAYLOAD-RETRIEVAL

## Objective
Make the real live Prefect single-packet pilot verifiable without false success when Prefect returns `state.data=None` for completed flow runs.

## Problem
The previous live pilot status reader depended on `flow_run.state.data`. Real Prefect API responses can mark results as untrackable, leaving `state.data=None` even when the flow run is `COMPLETED`. That made the pilot fail closed with `FLOW_RUN_PAYLOAD_MISSING`, but it also meant there was no deterministic retrieval path for the actual managed-runner result. The grace worker image also missed `importlib_metadata`, which `prefect worker start` needs in the Python 3.12 / Prefect 3.6.25 runtime.

## Solution
- Add `importlib_metadata` to the grace-worker image requirements.
- Pass `managed_result_payload_path` and `managed_result_payload_root` for managed packet submissions under `runtime_state_root/managed-runner-results`.
- Make `managed_packet_runner_flow` write bounded managed-runner JSON evidence atomically under the declared root.
- Make `create_bounded_prefect_status_reader()` use API `state.data` when present, and otherwise read the declared managed-result payload path from flow run parameters.
- Preserve fail-closed semantics: only `accepted|passed` domain status with `scope_verdict=passed` is `ok=True`; missing, unreadable, outside-root, malformed, incomplete, blocked, or failed payload evidence stays `ok=False`.

## Slice
- packet_id: `FEAT-GRACE-PREFECT-LIVE-PILOT-PAYLOAD-RETRIEVAL`
- feature_id: `FEAT-GRACE-PREFECT-LIVE-PILOT-PAYLOAD-RETRIEVAL`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- infra/grace-worker/requirements.txt
- prefect_grace/flows/managed_packet_runner_flow.py
- prefect_grace/platform/single_live_prefect_packet_pilot.py
- prefect_grace/platform/prefect_native_submission.py
- prefect_grace/platform/runtime_adapter.py
- prefect_grace/platform/managed_packet_runner.py
- prefect_grace/tasks/codex_launcher.py
- prefect_grace/tasks/managed_packet_artifacts.py
- prefect_grace/tasks/prefect_submitter.py
- tests/test_prefect_grace_single_live_prefect_packet_pilot.py
- tests/test_prefect_grace_prefect_native_submission.py
- tests/test_prefect_grace_managed_packet_runner.py
- tests/test_prefect_grace_managed_packet_runner_flow.py
- tests/test_prefect_grace_prefect_submitter_managed_packet.py
- tests/test_prefect_grace_*payload*.py
- prefect_grace/packets/FEAT-GRACE-PREFECT-LIVE-PILOT-PAYLOAD-RETRIEVAL/**

## Frozen Scope
- backend/**
- frontend/**
- .worktrees/**
- prefect_grace/executor_history.yaml
- prefect_grace/packet_registry.yaml
- prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**
- prefect_grace/packets/FEAT-ASTRO-ORDER-MANAGEMENT-SYSTEM/**

## Must Preserve
- Do not weaken fail-closed semantics for completed Prefect flow runs without inspectable payload evidence.
- Do not treat Prefect `COMPLETED` alone as domain success.
- Do not create live agents or real live Prefect pilot runs during packet-local tests.
- Do not write managed result payloads outside the declared runtime state root.
- Do not touch product backend/frontend code or unrelated runtime/untracked packet files.

## Verification
- Targeted pytest for status reader fallback, managed submission parameters, managed flow payload writing, and worker requirements dependency.
- Compile touched GRACE modules.
- Run `scripts/grace_lint.py` on touched GRACE modules.
- Validate this packet and its evidence manifest.
- Do not run real live Prefect pilot without reviewer approval.

## Expected Evidence
- `EVIDENCE/attempt-0001/evidence_manifest.json`
- `EVIDENCE/attempt-0002/evidence_manifest.json`
- `EVIDENCE/attempt-0002/rework_summary.md`
- `EVIDENCE/attempt-0003/evidence_manifest.json`
- `EVIDENCE/attempt-0003/rework_summary.md`
- Targeted pytest output showing pass count.
- Compileall output showing success.
- GRACE lint output showing success for touched GRACE modules.
- Packet/evidence validation output.
- Notes confirming no live Prefect pilot or Docker image rebuild was run.

## Escalation Triggers
- Status reader treats completed flow run as success without actual payload evidence.
- Managed result payload path can escape the declared runtime root.
- Fallback payload with missing/incomplete/malformed evidence is accepted.
- Worker requirements omit the Prefect runtime dependency.
