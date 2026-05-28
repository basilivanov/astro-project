# ############################################################################
# AI_HEADER: single_live_prefect_packet_pilot
# ROLE: Guarded one-packet Prefect-managed scratch pilot.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Plan or run one synthetic scratch packet through the managed Prefect packet runner.
# inputs: Project config path, explicit temp roots, live-agent gates, and optional test hooks.
# returns: SingleLivePrefectPacketPilotResult with bounded submission and scope evidence.
# side_effects: Writes synthetic packet/state under explicit temp roots and may submit one Prefect flow run after all gates.
# emitted_logs: None.
# error_behavior: Returns structured errors for gate, planning, submission, status, and scope failures.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - class: SingleLivePrefectPacketPilotResult
#   - function: run_single_live_prefect_packet_pilot
# END_MODULE_MAP

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
from typing import Any, Callable

from prefect_grace.platform.backlog_controller import BacklogController
from prefect_grace.platform.controller_backlog_bootstrap import build_backlog_bootstrap_plan
from prefect_grace.platform.live_opt_in_single_scratch_packet import (
    _ensure_synthetic_git_repo,
    _load_registry_map,
    _paths_outside_roots,
    _reset_temp_roots,
    _sync_result_to_dict,
    _validate_roots,
)
from prefect_grace.platform.prefect_native_submission import submit_ready_packets_to_prefect
from prefect_grace.platform.project_adapter import load_project_adapter
from prefect_grace.platform.scope_guard import validate_scope
from prefect_grace.tasks.prefect_submitter import MANAGED_PACKET_DEPLOYMENT_NAME

MODE = "single_live_prefect_packet_pilot"
FEATURE_ID = "FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT"
WAVE_ID = "W01"
PACKET_ID = "SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-SCRATCH"
EXTRA_PACKET_ID = "SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-EXTRA"
OPT_IN_TOKEN = "single-live-prefect"
SCRATCH_ALLOWED_SCOPE = "scratch/grace-single-live-prefect/**"
FROZEN_SCOPE = [
    "backend/**",
    "frontend/**",
    "prefect_grace/**",
    "scripts/**",
    "tools/**",
    "docker-compose*.yml",
    ".env",
]


# START_BLOCK: models


@dataclass(frozen=True)
class SingleLivePrefectPacketPilotResult:
    """Bounded result for the managed Prefect scratch packet pilot."""

    ok: bool
    project_key: str
    mode: str
    dry_run: bool
    opt_in_confirmed: bool
    state_root: str
    worktree_root: str
    packet_root: str
    selected_packet_id: str | None
    registry_before: dict[str, Any]
    registry_after: dict[str, Any]
    submit_plan: dict[str, Any]
    deployment_name: str | None
    work_queue_name: str | None
    flow_run_id: str | None
    flow_run_name: str | None
    flow_run_url: str | None
    prefect_runs_created: int
    live_agents_started: int
    domain_status: str | None
    scope_verdict: str | None
    changed_files: list[str]
    writes_outside_temp_roots: list[str]
    poll_events: list[dict[str, Any]]
    warnings: list[str]
    errors: list[dict[str, Any]]
    bootstrap_apply_count: int = 0
    sync_plan: dict[str, Any] = field(default_factory=dict)

    # START_FUNCTION_CONTRACT
    # name: to_dict
    # purpose: Serialize pilot result to a JSON-safe dictionary without secret tokens.
    # inputs:
    #   self: SingleLivePrefectPacketPilotResult instance.
    # returns: dict[str, Any] with all bounded result fields.
    # side_effects: None.
    # emitted_logs: None.
    # error_behavior: None.
    # END_FUNCTION_CONTRACT
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# END_BLOCK: models

# START_BLOCK: helpers


def _error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"code": code, "message": message, **extra}


def _result_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        return converted if isinstance(converted, dict) else {}
    if isinstance(value, dict):
        return dict(value)
    return {}


def _packet_markdown(packet_id: str) -> str:
    return f"""# Execution Packet: {packet_id}

## Objective
Write one deterministic scratch file through the managed Prefect packet runner.

## Slice
- packet_id: `{packet_id}`
- feature_id: `{FEATURE_ID}`
- wave_id: `{WAVE_ID}`
- status: `ready`

## Allowed Write Scope
- {SCRATCH_ALLOWED_SCOPE}

## Frozen Scope
{chr(10).join(f"- {scope}" for scope in FROZEN_SCOPE)}

## Must Preserve
- Live execution must remain bounded to this single synthetic scratch packet.
- No backend, frontend, platform, script, tool, compose, environment, source packet, or registry files may be edited outside temp roots.
- Git commit, push, and merge are disabled for this pilot.

## Verification
Run the managed Prefect packet runner with dry_run=false only after explicit live-agent opt-in gates.

## Expected Evidence
- Exactly one managed Prefect flow run is created.
- A deterministic file is written under `scratch/grace-single-live-prefect/`.
- Scope verdict confirms only scratch writes.

## Escalation Triggers
- More than one packet is selected.
- Any opt-in gate is missing for live mode.
- Any write lands outside explicit temporary roots or outside the scratch allowed scope.
"""


def _write_scratch_packet(packet_root: Path, *, extra_ready_packet: bool = False) -> Path:
    packets_dir = packet_root / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)

    packet_dir = packets_dir / PACKET_ID
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_markdown(PACKET_ID), encoding="utf-8")

    if extra_ready_packet:
        extra_dir = packets_dir / EXTRA_PACKET_ID
        extra_dir.mkdir(parents=True, exist_ok=True)
        (extra_dir / "EXECUTION_PACKET.md").write_text(_packet_markdown(EXTRA_PACKET_ID), encoding="utf-8")

    return packet_path


def _opt_in_errors(*, execute_agent: bool, acknowledge_live_agent: bool, opt_in_token: str | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not execute_agent:
        errors.append(_error("LIVE_PREFECT_EXECUTE_AGENT_REQUIRED", "--execute-agent is required for live Prefect pilot execution."))
    if not acknowledge_live_agent:
        errors.append(_error("LIVE_PREFECT_ACK_REQUIRED", "--i-understand-live-agent is required for live Prefect pilot execution."))
    if opt_in_token != OPT_IN_TOKEN:
        errors.append(_error("LIVE_PREFECT_TOKEN_REQUIRED", "Required live Prefect opt-in token is missing or invalid."))
    return errors


def _empty_result(
    *,
    ok: bool,
    project_key: str,
    dry_run: bool,
    opt_in_confirmed: bool,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    errors: list[dict[str, Any]],
    warnings: list[str] | None = None,
) -> SingleLivePrefectPacketPilotResult:
    return SingleLivePrefectPacketPilotResult(
        ok=ok,
        project_key=project_key,
        mode=MODE,
        dry_run=dry_run,
        opt_in_confirmed=opt_in_confirmed,
        state_root=str(state_root),
        worktree_root=str(worktree_root),
        packet_root=str(packet_root),
        selected_packet_id=None,
        registry_before={},
        registry_after={},
        submit_plan={},
        deployment_name=None,
        work_queue_name=None,
        flow_run_id=None,
        flow_run_name=None,
        flow_run_url=None,
        prefect_runs_created=0,
        live_agents_started=0,
        domain_status=None,
        scope_verdict=None,
        changed_files=[],
        writes_outside_temp_roots=[],
        poll_events=[],
        warnings=warnings or [],
        errors=errors,
    )


def _submission_record_fields(record: Any) -> dict[str, Any]:
    if hasattr(record, "to_dict"):
        return record.to_dict()
    return dict(record)


def _status_reader_result(
    *,
    status_reader: Callable[..., Any] | None,
    flow_run_id: str | None,
    packet_id: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if status_reader is None:
        return {
            "ok": False,
            "domain_status": None,
            "scope_verdict": "pending_prefect_flow",
            "live_agents_started": 0,
            "changed_files": [],
            "poll_events": [],
            "errors": [
                _error(
                    "LIVE_PREFECT_FINAL_EVIDENCE_PENDING",
                    "Prefect flow was submitted, but final managed-runner domain and scope evidence is not available in this process.",
                )
            ],
        }
    return _result_dict(
        status_reader(
            flow_run_id=flow_run_id,
            packet_id=packet_id,
            timeout_seconds=timeout_seconds,
        )
    )


# END_BLOCK: helpers

# START_BLOCK: pilot


# START_FUNCTION_CONTRACT
# name: run_single_live_prefect_packet_pilot
# purpose: Plan or run one synthetic scratch packet through managed Prefect submission.
# inputs:
#   project_config: Path to project config.
#   state_root: Explicit temporary state root.
#   worktree_root: Explicit temporary worktree root.
#   packet_root: Explicit temporary packet source root.
#   dry_run: Safe default, plans only and creates zero Prefect flow runs.
#   execute_agent: Required live-agent execution flag for non-dry-run mode.
#   acknowledge_live_agent: Required operator acknowledgement for non-dry-run mode.
#   opt_in_token: Required opt-in token for non-dry-run mode, or None to read environment.
#   timeout_seconds: Submission/status timeout seconds.
#   submitter: Optional Prefect submitter hook for tests.
#   status_reader: Optional bounded status reader hook for tests.
#   extra_ready_packet: Test hook proving multi-packet plans fail closed.
# returns: SingleLivePrefectPacketPilotResult.
# side_effects: Writes temp packet/state and may submit one Prefect managed packet flow run after all gates.
# emitted_logs: None.
# error_behavior: Returns structured errors instead of raising for expected pilot failures.
# END_FUNCTION_CONTRACT
def run_single_live_prefect_packet_pilot(
    *,
    project_config: Path,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    dry_run: bool = True,
    execute_agent: bool = False,
    acknowledge_live_agent: bool = False,
    opt_in_token: str | None = None,
    timeout_seconds: int = 1800,
    submitter: Callable[..., dict[str, Any]] | None = None,
    status_reader: Callable[..., Any] | None = None,
    extra_ready_packet: bool = False,
) -> SingleLivePrefectPacketPilotResult:
    base_adapter = load_project_adapter(project_config)
    token = opt_in_token if opt_in_token is not None else os.environ.get("GRACE_LIVE_PREFECT_PACKET_OPT_IN")

    if not dry_run:
        gate_errors = _opt_in_errors(
            execute_agent=execute_agent,
            acknowledge_live_agent=acknowledge_live_agent,
            opt_in_token=token,
        )
        if gate_errors:
            return _empty_result(
                ok=False,
                project_key=base_adapter.project_key,
                dry_run=dry_run,
                opt_in_confirmed=False,
                state_root=state_root,
                worktree_root=worktree_root,
                packet_root=packet_root,
                errors=gate_errors,
            )

    root_errors = _validate_roots(
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        repo_root=Path(base_adapter.repo_root),
    )
    if root_errors:
        return _empty_result(
            ok=False,
            project_key=base_adapter.project_key,
            dry_run=dry_run,
            opt_in_confirmed=not dry_run,
            state_root=state_root,
            worktree_root=worktree_root,
            packet_root=packet_root,
            errors=root_errors,
        )

    warnings: list[str] = []
    errors: list[dict[str, Any]] = []
    _reset_temp_roots(state_root, worktree_root, packet_root)
    _ensure_synthetic_git_repo(packet_root)
    packet_path = _write_scratch_packet(packet_root, extra_ready_packet=extra_ready_packet)

    adapter = load_project_adapter(
        project_config,
        overrides={
            "repo_root": str(packet_root),
            "packets_dir": "packets",
            "runtime_state_root": str(state_root),
            "artifact_root": str(state_root / "artifacts"),
            "worktree_root": str(worktree_root),
        },
    )

    bootstrap_plan = build_backlog_bootstrap_plan(adapter, dry_run=False)
    warnings.extend(bootstrap_plan.warnings)
    errors.extend(_error("BOOTSTRAP_APPLY_FAILED", str(err)) for err in bootstrap_plan.errors)
    registry_before = _load_registry_map(state_root)

    sync_result = BacklogController.sync(adapter, dry_run=True)
    warnings.extend(sync_result.warnings)
    errors.extend(_error("SYNC_DRY_RUN_FAILED", str(err)) for err in sync_result.errors)

    dry_submit = submit_ready_packets_to_prefect(
        project=adapter,
        dry_run=True,
        limit=None,
        execute_agent=True,
        timeout_seconds=timeout_seconds,
        worktree_root=worktree_root,
        submitter=None,
        runner_kind="managed",
    )
    submit_plan = dry_submit.to_dict()
    submit_plan["packets_to_submit"] = list(dry_submit.packets_planned)
    warnings.extend(dry_submit.warnings)
    errors.extend(dry_submit.errors)

    selected_packet_id = dry_submit.packets_planned[0] if dry_submit.packets_planned == [PACKET_ID] else None
    if dry_submit.packets_planned != [PACKET_ID]:
        errors.append(
            _error(
                "LIVE_PREFECT_PACKET_COUNT_INVALID",
                "Managed Prefect dry-run plan must select exactly the synthetic scratch packet.",
                packets_planned=list(dry_submit.packets_planned),
            )
        )

    deployment_name = None
    work_queue_name = None
    flow_run_id = None
    flow_run_name = None
    flow_run_url = None
    prefect_runs_created = 0
    live_agents_started = 0
    domain_status = None
    scope_verdict = None
    changed_files: list[str] = []
    poll_events: list[dict[str, Any]] = []

    if dry_submit.records:
        record_data = _submission_record_fields(dry_submit.records[0])
        deployment_name = record_data.get("deployment_name")
        work_queue_name = record_data.get("work_queue_name")
        flow_run_name = record_data.get("flow_run_name")

    if not dry_run and selected_packet_id and not errors:
        if submitter is None:
            from prefect_grace.platform.runtime_adapter import ManagedPacketSubmitter
            submitter = ManagedPacketSubmitter()

        submission = submit_ready_packets_to_prefect(
            project=adapter,
            dry_run=False,
            limit=1,
            execute_agent=True,
            timeout_seconds=timeout_seconds,
            worktree_root=worktree_root,
            submitter=submitter,
            runner_kind="managed",
        )
        errors.extend(submission.errors)
        if len(submission.records) != 1:
            errors.append(_error("LIVE_PREFECT_SUBMISSION_COUNT_INVALID", f"Expected one submission record; got {len(submission.records)}."))
        elif not submission.errors:
            record = submission.records[0]
            deployment_name = record.deployment_name
            work_queue_name = record.work_queue_name
            flow_run_id = record.flow_run_id
            flow_run_name = record.flow_run_name
            flow_run_url = record.url
            if record.packet_id != PACKET_ID:
                errors.append(_error("LIVE_PREFECT_WRONG_PACKET_SUBMITTED", f"Expected {PACKET_ID}; got {record.packet_id}."))
            if record.deployment_name != MANAGED_PACKET_DEPLOYMENT_NAME:
                errors.append(_error("LIVE_PREFECT_UNEXPECTED_DEPLOYMENT", f"Expected {MANAGED_PACKET_DEPLOYMENT_NAME}; got {record.deployment_name}."))
            if record.status != "submitted":
                errors.append(_error("LIVE_PREFECT_NOT_SUBMITTED", record.error or record.status))
            if record.status == "submitted":
                prefect_runs_created = 1
                status_result = _status_reader_result(
                    status_reader=status_reader,
                    flow_run_id=flow_run_id,
                    packet_id=PACKET_ID,
                    timeout_seconds=timeout_seconds,
                )
                errors.extend(list(status_result.get("errors") or []))
                live_agents_started = int(status_result.get("live_agents_started") or status_result.get("agent_launch_count") or 0)
                domain_status = status_result.get("domain_status")
                scope_verdict = status_result.get("scope_verdict")
                changed_files = list(status_result.get("changed_files") or [])
                poll_events = list(status_result.get("poll_events") or [])
                if not status_result.get("ok", False):
                    errors.append(_error("LIVE_PREFECT_STATUS_NOT_OK", "Managed Prefect status reader did not return ok=true."))

    if status_reader is not None and changed_files:
        scope_result = validate_scope(
            changed_files,
            [SCRATCH_ALLOWED_SCOPE],
            FROZEN_SCOPE,
            repo_root=packet_root,
        )
        if not scope_result.ok:
            errors.append(
                _error(
                    "LIVE_PREFECT_CHANGED_FILES_OUTSIDE_SCRATCH",
                    "Managed Prefect pilot changed files outside the synthetic scratch allowed scope.",
                    scope_result=scope_result.to_dict(),
                )
            )

    registry_after = _load_registry_map(state_root)
    touched_paths = [
        state_root / "state" / "packet_registry.yaml",
        packet_root / "packets",
        worktree_root,
    ]
    writes_outside_temp_roots = _paths_outside_roots(touched_paths, [state_root, worktree_root, packet_root])
    if writes_outside_temp_roots:
        errors.append(_error("WRITE_OUTSIDE_TEMP_ROOTS", "Pilot detected writes outside temp roots."))

    ok = (
        not errors
        and selected_packet_id == PACKET_ID
        and not writes_outside_temp_roots
        and (
            dry_run
            or (
                prefect_runs_created == 1
                and live_agents_started == 1
                and domain_status in {"accepted", "passed"}
                and scope_verdict == "passed"
            )
        )
    )

    return SingleLivePrefectPacketPilotResult(
        ok=ok,
        project_key=adapter.project_key,
        mode=MODE,
        dry_run=dry_run,
        opt_in_confirmed=dry_run or not _opt_in_errors(
            execute_agent=execute_agent,
            acknowledge_live_agent=acknowledge_live_agent,
            opt_in_token=token,
        ),
        state_root=str(state_root),
        worktree_root=str(worktree_root),
        packet_root=str(packet_root),
        selected_packet_id=selected_packet_id,
        registry_before=registry_before,
        registry_after=registry_after,
        submit_plan=submit_plan,
        deployment_name=deployment_name,
        work_queue_name=work_queue_name,
        flow_run_id=flow_run_id,
        flow_run_name=flow_run_name,
        flow_run_url=flow_run_url,
        prefect_runs_created=prefect_runs_created,
        live_agents_started=live_agents_started,
        domain_status=domain_status,
        scope_verdict=scope_verdict,
        changed_files=changed_files,
        writes_outside_temp_roots=writes_outside_temp_roots,
        poll_events=poll_events,
        warnings=warnings,
        errors=errors,
        bootstrap_apply_count=bootstrap_plan.apply_count,
        sync_plan=_sync_result_to_dict(sync_result),
    )


# END_BLOCK: pilot
