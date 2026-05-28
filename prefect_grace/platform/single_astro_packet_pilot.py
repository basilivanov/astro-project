# ############################################################################
# AI_HEADER: single_astro_packet_pilot
# ROLE: Guarded one-packet Astro pilot for real product packets.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Plan or run one low-risk real Astro packet through the managed Prefect packet runner.
# inputs: Project config path, explicit temp roots, live-agent gates, and optional test hooks.
# returns: SingleAstroPacketPilotResult with bounded submission and scope evidence.
# side_effects: May submit one Prefect flow run after all gates; no Git mutation.
# emitted_logs: None.
# error_behavior: Returns structured errors for gate, planning, submission, status, and scope failures.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - class: SingleAstroPacketPilotResult
#   - function: run_single_astro_packet_pilot
#   - function: _is_low_risk_candidate
# END_MODULE_MAP

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
from typing import Any, Callable

from prefect_grace.platform.backlog_controller import BacklogController
from prefect_grace.platform.controller_backlog_bootstrap import build_backlog_bootstrap_plan
from prefect_grace.platform.live_opt_in_single_scratch_packet import (
    _load_registry_map,
    _paths_outside_roots,
    _sync_result_to_dict,
    _validate_roots,
)
from prefect_grace.platform.prefect_native_submission import submit_ready_packets_to_prefect
from prefect_grace.platform.project_adapter import load_project_adapter
from prefect_grace.platform.scope_guard import validate_scope
from prefect_grace.platform.single_live_prefect_packet_pilot import create_bounded_prefect_status_reader
from prefect_grace.tasks.prefect_submitter import MANAGED_PACKET_DEPLOYMENT_NAME

MODE = "single_astro_packet_pilot"
FEATURE_ID = "FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT"
WAVE_ID = "W01"
OPT_IN_TOKEN = "single-astro-packet"


@dataclass
class SingleAstroPacketPilotResult:
    """Result from single Astro packet pilot."""

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
    warnings: list[dict[str, str]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    bootstrap_apply_count: int = 0
    sync_plan: dict[str, Any] = field(default_factory=dict)


def _is_low_risk_candidate(packet: dict[str, Any]) -> tuple[bool, str | None]:
    """Check if packet is a low-risk candidate for first Astro pilot.

    Returns (is_low_risk, rejection_reason).
    """
    packet_id = packet.get("packet_id", "")
    status = packet.get("status", "")
    allowed_scope = packet.get("allowed_write_scope", [])

    # Must be ready
    if status != "ready":
        return False, f"Packet {packet_id} status is {status}, not ready"

    # Must have allowed scope
    if not allowed_scope:
        return False, f"Packet {packet_id} has no allowed_write_scope"

    # Reject if scope is too broad (heuristic: more than 20 paths or includes backend/frontend root)
    if len(allowed_scope) > 20:
        return False, f"Packet {packet_id} has broad scope ({len(allowed_scope)} paths)"

    # Check for risky patterns
    for scope_path in allowed_scope:
        scope_lower = scope_path.lower()
        if scope_lower.startswith("/opt/astro-project/backend") and "**" in scope_path:
            return False, f"Packet {packet_id} has broad backend scope: {scope_path}"
        if scope_lower.startswith("/opt/astro-project/frontend") and "**" in scope_path:
            return False, f"Packet {packet_id} has broad frontend scope: {scope_path}"
        if "/scripts/pipeline.py" in scope_lower:
            return False, f"Packet {packet_id} modifies pipeline.py"
        if "docker-compose" in scope_lower:
            return False, f"Packet {packet_id} modifies Docker compose"

    return True, None


def run_single_astro_packet_pilot(
    project_path: str | Path,
    state_root: str | Path,
    worktree_root: str | Path,
    packet_root: str | Path,
    dry_run: bool = True,
    execute_agent: bool = False,
    acknowledge_live_agent: bool = False,
    opt_in_token: str | None = None,
    timeout_seconds: int = 300,
    packet_id: str | None = None,
    submitter: Callable | None = None,
    status_reader: Callable | None = None,
) -> SingleAstroPacketPilotResult:
    """Run single Astro packet pilot.

    Args:
        project_path: Path to project.yaml
        state_root: Root for state files
        worktree_root: Root for worktrees
        packet_root: Root for packet files
        dry_run: If True, plan only without submission
        execute_agent: If True, allow agent execution
        acknowledge_live_agent: If True, acknowledge live agent risk
        opt_in_token: Required token for live execution
        timeout_seconds: Timeout for status polling
        packet_id: Explicit packet ID to run (optional)
        submitter: Test hook for Prefect submission
        status_reader: Test hook for status reading

    Returns:
        SingleAstroPacketPilotResult with bounded evidence
    """
    # START_FUNCTION_CONTRACT
    # name: run_single_astro_packet_pilot
    # purpose: Plan or run one low-risk real Astro packet through managed Prefect runner.
    # inputs: project_path (Path), state/worktree/packet roots (Path), dry_run (bool), execute_agent (bool), acknowledge_live_agent (bool), opt_in_token (str|None), timeout_seconds (int), packet_id (str|None), submitter (Callable|None), status_reader (Callable|None).
    # returns: SingleAstroPacketPilotResult with bounded submission and scope evidence.
    # side_effects: May submit one Prefect flow run after all gates; no Git mutation.
    # emitted_logs: None.
    # error_behavior: Returns structured errors for gate, planning, submission, status, and scope failures.
    # END_FUNCTION_CONTRACT
    project_path = Path(project_path)
    state_root = Path(state_root)
    worktree_root = Path(worktree_root)
    packet_root = Path(packet_root)

    errors = []
    warnings = []

    # Validate roots
    repo_root = Path.cwd()
    root_validation_errors = _validate_roots(
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        repo_root=repo_root,
    )
    if root_validation_errors:
        return SingleAstroPacketPilotResult(
            ok=False,
            project_key="",
            mode=MODE,
            dry_run=dry_run,
            opt_in_confirmed=False,
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
            errors=root_validation_errors,
        )

    # Load project
    try:
        adapter = load_project_adapter(project_path)
        project_key = adapter.project_key
    except Exception as e:
        return SingleAstroPacketPilotResult(
            ok=False,
            project_key="",
            mode=MODE,
            dry_run=dry_run,
            opt_in_confirmed=False,
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
            errors=[{"code": "PROJECT_LOAD_FAILED", "message": str(e)}],
        )

    # Check opt-in gates for live execution
    opt_in_confirmed = True
    if not dry_run and execute_agent:
        if not acknowledge_live_agent:
            errors.append({"code": "LIVE_AGENT_NOT_ACKNOWLEDGED", "message": "Live agent execution requires --i-understand-live-agent"})
            opt_in_confirmed = False

        expected_token = os.environ.get("GRACE_ASTRO_PACKET_OPT_IN", "")
        if expected_token != OPT_IN_TOKEN:
            errors.append({"code": "OPT_IN_TOKEN_MISMATCH", "message": f"Expected GRACE_ASTRO_PACKET_OPT_IN={OPT_IN_TOKEN}"})
            opt_in_confirmed = False

        if opt_in_token != OPT_IN_TOKEN:
            errors.append({"code": "CLI_OPT_IN_MISMATCH", "message": f"CLI opt-in token must be {OPT_IN_TOKEN}"})
            opt_in_confirmed = False

    if not opt_in_confirmed:
        return SingleAstroPacketPilotResult(
            ok=False,
            project_key=project_key,
            mode=MODE,
            dry_run=dry_run,
            opt_in_confirmed=False,
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
            errors=errors,
        )

    # Load registry
    try:
        registry_map = _load_registry_map(adapter)
    except Exception as e:
        return SingleAstroPacketPilotResult(
            ok=False,
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
            errors=[{"code": "REGISTRY_LOAD_FAILED", "message": str(e)}],
        )

    registry_before = {k: v for k, v in registry_map.items()}

    # Select candidate packet
    selected_packet_id = None
    if packet_id:
        # Explicit packet ID
        if packet_id not in registry_map:
            return SingleAstroPacketPilotResult(
                ok=False,
                project_key=project_key,
                mode=MODE,
                dry_run=dry_run,
                opt_in_confirmed=opt_in_confirmed,
                state_root=str(state_root),
                worktree_root=str(worktree_root),
                packet_root=str(packet_root),
                selected_packet_id=packet_id,
                registry_before=registry_before,
                registry_after=registry_before,
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
                errors=[{"code": "PACKET_NOT_FOUND", "message": f"Packet {packet_id} not in registry"}],
            )

        packet = registry_map[packet_id]
        is_low_risk, rejection_reason = _is_low_risk_candidate(packet)
        if not is_low_risk:
            return SingleAstroPacketPilotResult(
                ok=False,
                project_key=project_key,
                mode=MODE,
                dry_run=dry_run,
                opt_in_confirmed=opt_in_confirmed,
                state_root=str(state_root),
                worktree_root=str(worktree_root),
                packet_root=str(packet_root),
                selected_packet_id=packet_id,
                registry_before=registry_before,
                registry_after=registry_before,
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
                errors=[{"code": "PACKET_NOT_LOW_RISK", "message": rejection_reason}],
            )

        selected_packet_id = packet_id
    else:
        # Auto-select first low-risk ready packet
        for pid, packet in registry_map.items():
            is_low_risk, _ = _is_low_risk_candidate(packet)
            if is_low_risk:
                selected_packet_id = pid
                break

        if not selected_packet_id:
            return SingleAstroPacketPilotResult(
                ok=False,
                project_key=project_key,
                mode=MODE,
                dry_run=dry_run,
                opt_in_confirmed=opt_in_confirmed,
                state_root=str(state_root),
                worktree_root=str(worktree_root),
                packet_root=str(packet_root),
                selected_packet_id=None,
                registry_before=registry_before,
                registry_after=registry_before,
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
                errors=[{"code": "NO_LOW_RISK_CANDIDATE", "message": "No low-risk ready packets found in registry"}],
            )

    # Submit to Prefect
    try:
        if submitter:
            # Test hook
            submit_result = submitter(
                project_key=project_key,
                packet_ids=[selected_packet_id],
                dry_run=dry_run,
            )
        else:
            # Real submission
            submit_result = submit_ready_packets_to_prefect(
                project_key=project_key,
                packet_ids=[selected_packet_id],
                deployment_name=MANAGED_PACKET_DEPLOYMENT_NAME,
                work_queue_name=None,
                dry_run=dry_run,
            )
    except Exception as e:
        return SingleAstroPacketPilotResult(
            ok=False,
            project_key=project_key,
            mode=MODE,
            dry_run=dry_run,
            opt_in_confirmed=opt_in_confirmed,
            state_root=str(state_root),
            worktree_root=str(worktree_root),
            packet_root=str(packet_root),
            selected_packet_id=selected_packet_id,
            registry_before=registry_before,
            registry_after=registry_before,
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
            errors=[{"code": "SUBMISSION_FAILED", "message": str(e)}],
        )

    submit_plan_dict = asdict(submit_result) if hasattr(submit_result, "__dataclass_fields__") else submit_result

    # Extract flow run info
    flow_run_id = None
    flow_run_name = None
    flow_run_url = None
    deployment_name = MANAGED_PACKET_DEPLOYMENT_NAME
    work_queue_name = None
    prefect_runs_created = 0

    if submit_result.ok and submit_result.records:
        record = submit_result.records[0]
        flow_run_id = record.get("flow_run_id")
        flow_run_name = record.get("flow_run_name")
        flow_run_url = record.get("url")
        if flow_run_id:
            prefect_runs_created = 1

    # Poll status if live execution
    domain_status = None
    scope_verdict = None
    changed_files = []
    poll_events = []
    live_agents_started = 0

    if not dry_run and execute_agent and flow_run_id:
        try:
            if status_reader:
                # Test hook
                status_result = status_reader(
                    flow_run_id=flow_run_id,
                    packet_id=selected_packet_id,
                    timeout_seconds=timeout_seconds,
                )
            else:
                # Real status reader - use bounded reader with None client
                # The bounded reader will fail gracefully if client is needed
                reader = create_bounded_prefect_status_reader(None)
                status_result = reader(
                    flow_run_id=flow_run_id,
                    packet_id=selected_packet_id,
                    timeout_seconds=timeout_seconds,
                )

            domain_status = status_result.get("domain_status")
            scope_verdict = status_result.get("scope_verdict")
            changed_files = status_result.get("changed_files", [])
            poll_events = status_result.get("poll_events", [])
            live_agents_started = status_result.get("live_agents_started", 0)

            if not status_result.get("ok"):
                errors.extend(status_result.get("errors", []))
        except Exception as e:
            errors.append({"code": "STATUS_READ_FAILED", "message": str(e)})
            domain_status = None
            scope_verdict = "status_read_failed"

    # Check writes outside temp roots
    writes_outside_temp_roots = _paths_outside_roots(changed_files, [str(state_root), str(worktree_root), str(packet_root)])

    # Final ok status
    final_ok = submit_result.ok and (dry_run or (domain_status in ("accepted", "passed") and scope_verdict == "passed"))

    return SingleAstroPacketPilotResult(
        ok=final_ok,
        project_key=project_key,
        mode=MODE,
        dry_run=dry_run,
        opt_in_confirmed=opt_in_confirmed,
        state_root=str(state_root),
        worktree_root=str(worktree_root),
        packet_root=str(packet_root),
        selected_packet_id=selected_packet_id,
        registry_before=registry_before,
        registry_after=registry_before,
        submit_plan=submit_plan_dict,
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
    )
