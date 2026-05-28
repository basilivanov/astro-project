"""
# ============================================================================
# AI_HEADER: GRACE End-To-End Packet Runner Module
# ============================================================================
#
# This module provides the orchestration seam that wires together existing
# GRACE primitives into a single end-to-end packet execution flow.
#
# Key Concepts:
# - Orchestration only (no reimplementation of primitives)
# - Dry-run by default (no live agents unless explicitly enabled)
# - Fake verifier/reviewer outputs for testing handoff
# - One packet per invocation (no batch/dependency queue)
# - No merge/push/squash/delete-worktree operations
# - Core runner works without Prefect server
# - Domain status priority: coder failures block handoff
#
# Module Dependencies:
# - prefect_grace.platform.managed_packet_runner
# - prefect_grace.platform.verifier_reviewer_handoff
# - prefect_grace.platform.packet_parser
# - No Prefect imports (pure orchestration logic)
#
# ============================================================================
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from prefect_grace.platform.managed_packet_runner import (
    run_managed_packet,
    ManagedPacketRunResult,
)
from prefect_grace.platform.status_model import (
    DomainStatus,
    apply_domain_result_to_registry,
)
from prefect_grace.platform.verifier_reviewer_handoff import (
    run_verifier_reviewer_handoff,
    PacketHandoffResult,
)
from prefect_grace.platform.packet_parser import parse_packet_markdown

# START_MODULE_CONTRACT
# Module: e2e_packet_runner
# Purpose: Orchestrate end-to-end packet execution from coder to verifier to reviewer
# Exports: E2EPacketRunnerResult, run_e2e_packet
# Dependencies: managed_packet_runner, verifier_reviewer_handoff, packet_parser
# Constraints: Dry-run by default, no live agents, no merge/push/squash, works without Prefect
# END_MODULE_CONTRACT

# START_MODULE_MAP
# Block: models - E2EPacketRunnerResult dataclass
# Block: fake_launchers - Fake verifier/reviewer launcher helpers
# Block: orchestrator - run_e2e_packet function
# END_MODULE_MAP

# START_BLOCK: models

@dataclass(frozen=True)
class E2EPacketRunnerResult:
    """Result of end-to-end packet execution.

    Fields:
    - ok: True if domain_status is "accepted"
    - packet_id: Packet identifier
    - attempt: Attempt number
    - runtime_status: Execution status (started, completed, failed)
    - domain_status: Packet outcome status
    - registry_status: Registry state implied by domain_status
    - registry_reason: Reason for the registry transition
    - registry_transition: Full serialized StatusTransition
    - worktree_path: Path to worktree (None if worktree creation failed)
    - branch_name: Git branch name (None if worktree creation failed)
    - executor_id: Executor identifier (None if not selected)
    - managed_runner_result: ManagedPacketRunResult as dict
    - handoff_result: PacketHandoffResult as dict (None if handoff not run)
    - artifact_paths: List of artifact paths from both phases
    - errors: List of error messages
    """
    ok: bool
    packet_id: str
    attempt: int
    runtime_status: str
    domain_status: str
    registry_status: str
    registry_reason: str
    registry_transition: dict[str, Any]
    worktree_path: str | None
    branch_name: str | None
    executor_id: str | None
    managed_runner_result: dict[str, Any]
    handoff_result: dict[str, Any] | None
    artifact_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # START_FUNCTION_CONTRACT
    # Function: to_dict
    # Purpose: Serialize E2EPacketRunnerResult to dict for JSON output
    # Args: None (instance method)
    # Returns: Dict with all result fields
    # Inputs: self
    # Side_effects: None (pure function)
    # Emitted_logs: None
    # Error_behavior: Never raises
    # END_FUNCTION_CONTRACT
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        return {
            "ok": self.ok,
            "packet_id": self.packet_id,
            "attempt": self.attempt,
            "runtime_status": self.runtime_status,
            "domain_status": self.domain_status,
            "registry_status": self.registry_status,
            "registry_reason": self.registry_reason,
            "registry_transition": dict(self.registry_transition),
            "worktree_path": self.worktree_path,
            "branch_name": self.branch_name,
            "executor_id": self.executor_id,
            "managed_runner_result": dict(self.managed_runner_result),
            "handoff_result": dict(self.handoff_result) if self.handoff_result else None,
            "artifact_paths": list(self.artifact_paths),
            "errors": list(self.errors),
        }

# END_BLOCK: models

# START_BLOCK: fake_launchers

# START_FUNCTION_CONTRACT
# Function: _create_fake_verifier_launcher
# Purpose: Create fake verifier launcher for testing handoff without live agents
# Args:
#   - fake_output_path: Optional path to fake verifier output file
# Returns: Callable that returns dict with raw_output containing verifier marker
# Inputs: Optional file path with fake verifier output
# Side_effects: Reads file if provided
# Emitted_logs: None
# Error_behavior: Returns default fake output if file not found or read fails
# END_FUNCTION_CONTRACT
def _create_fake_verifier_launcher(fake_output_path: Path | None) -> Callable[..., dict[str, Any]]:
    """
    Create fake verifier launcher for testing.

    Returns a callable that produces fake verifier output with
    FINAL_VERIFIER_EVIDENCE_JSON marker.
    """
    # START_FUNCTION_CONTRACT
    # Function: launcher (nested)
    # Purpose: Fake verifier launcher callable
    # Args: **kwargs (packet_id, etc.)
    # Returns: Dict with raw_output field
    # Inputs: kwargs from handoff caller
    # Side_effects: None
    # Emitted_logs: None
    # Error_behavior: Never raises
    # END_FUNCTION_CONTRACT
    def launcher(**kwargs: Any) -> dict[str, Any]:
        if fake_output_path and fake_output_path.exists():
            try:
                raw_output = fake_output_path.read_text()
            except Exception:
                raw_output = _default_fake_verifier_output(kwargs.get("packet_id", "UNKNOWN"))
        else:
            raw_output = _default_fake_verifier_output(kwargs.get("packet_id", "UNKNOWN"))

        return {"raw_output": raw_output}

    return launcher


# START_FUNCTION_CONTRACT
# Function: _create_fake_reviewer_launcher
# Purpose: Create fake reviewer launcher for testing handoff without live agents
# Args:
#   - fake_output_path: Optional path to fake reviewer output file
# Returns: Callable that returns dict with raw_output containing reviewer marker
# Inputs: Optional file path with fake reviewer output
# Side_effects: Reads file if provided
# Emitted_logs: None
# Error_behavior: Returns default fake output if file not found or read fails
# END_FUNCTION_CONTRACT
def _create_fake_reviewer_launcher(fake_output_path: Path | None) -> Callable[..., dict[str, Any]]:
    """
    Create fake reviewer launcher for testing.

    Returns a callable that produces fake reviewer output with
    FINAL_PACKET_DECISION_JSON marker.
    """
    # START_FUNCTION_CONTRACT
    # Function: launcher (nested)
    # Purpose: Fake reviewer launcher callable
    # Args: **kwargs (packet_id, etc.)
    # Returns: Dict with raw_output field
    # Inputs: kwargs from handoff caller
    # Side_effects: None
    # Emitted_logs: None
    # Error_behavior: Never raises
    # END_FUNCTION_CONTRACT
    def launcher(**kwargs: Any) -> dict[str, Any]:
        if fake_output_path and fake_output_path.exists():
            try:
                raw_output = fake_output_path.read_text()
            except Exception:
                raw_output = _default_fake_reviewer_output(kwargs.get("packet_id", "UNKNOWN"))
        else:
            raw_output = _default_fake_reviewer_output(kwargs.get("packet_id", "UNKNOWN"))

        return {"raw_output": raw_output}

    return launcher


# START_FUNCTION_CONTRACT
# Function: _default_fake_verifier_output
# Purpose: Generate default fake verifier output with accepted evidence
# Args:
#   - packet_id: Packet identifier
# Returns: String with FINAL_VERIFIER_EVIDENCE_JSON marker
# Inputs: packet_id
# Side_effects: None (pure function)
# Emitted_logs: None
# Error_behavior: Never raises
# END_FUNCTION_CONTRACT
def _default_fake_verifier_output(packet_id: str) -> str:
    """Generate default fake verifier output with accepted evidence."""
    return f"""
Verifier dry-run output for packet {packet_id}.

FINAL_VERIFIER_EVIDENCE_JSON
{{
  "packet_id": "{packet_id}",
  "generated_by": "verifier",
  "requirement_results": [
    {{
      "id": "EV-FAKE-001",
      "status": "collected",
      "stage": "packet_local",
      "producer": "fake_verifier",
      "artifact_paths": [],
      "summary": "Fake evidence for dry-run testing"
    }}
  ]
}}
END_FINAL_VERIFIER_EVIDENCE_JSON
"""


# START_FUNCTION_CONTRACT
# Function: _default_fake_reviewer_output
# Purpose: Generate default fake reviewer output with accepted verdict
# Args:
#   - packet_id: Packet identifier
# Returns: String with FINAL_PACKET_DECISION_JSON marker
# Inputs: packet_id
# Side_effects: None (pure function)
# Emitted_logs: None
# Error_behavior: Never raises
# END_FUNCTION_CONTRACT
def _default_fake_reviewer_output(packet_id: str) -> str:
    """Generate default fake reviewer output with accepted verdict."""
    return f"""
Reviewer dry-run output for packet {packet_id}.

FINAL_PACKET_DECISION_JSON
{{
  "packet_verdict": "accepted",
  "route_classification": null,
  "rework_mode": null,
  "reasons": []
}}
END_FINAL_PACKET_DECISION_JSON
"""

# END_BLOCK: fake_launchers

# START_BLOCK: real_launchers

# START_FUNCTION_CONTRACT
# Function: _create_real_verifier_launcher
# Purpose: Create real verifier launcher that runs live agent via codex
# Args:
#   - packet_id: Base packet identifier
#   - project: Project config with runtime_state_root
#   - timeout_seconds: Agent timeout
# Returns: Callable that launches verifier agent and returns dict with raw_output
# Inputs: Packet ID, project config, timeout
# Side_effects: Launches live codex agent, writes to state store
# Emitted_logs: Agent execution logs
# Error_behavior: Raises exception if agent launch fails
# END_FUNCTION_CONTRACT
def _create_real_verifier_launcher(
    packet_id: str,
    project: Any,
    timeout_seconds: int,
) -> Callable[..., dict[str, Any]]:
    """Create real verifier launcher that runs live agent."""
    from prefect_grace.tasks.codex_launcher import _launch_codex_for_packet
    from prefect_grace.platform.state_store import PacketRegistryStore

    def launcher(**kwargs: Any) -> dict[str, Any]:
        # Create temporary verifier packet record
        verifier_packet_id = f"{packet_id}-VERIFIER"
        runtime_state_root = getattr(project, "runtime_state_root", None)

        # Register verifier packet in state store
        if runtime_state_root:
            store = PacketRegistryStore(Path(runtime_state_root) / "state")
            coder_result = kwargs.get("coder_result", {})
            packet_path = kwargs.get("packet_file")

            # Create verifier packet record
            verifier_record = {
                "packet_id": verifier_packet_id,
                "feature_id": packet_id.rsplit("-W", 1)[0] if "-W" in packet_id else packet_id,
                "wave_id": "W01",
                "path": str(packet_path) if packet_path else "",
                "role": "verifier",
                "reasoning": "high",
            }
            store.upsert_packet(verifier_record)

        # Launch verifier agent
        result = _launch_codex_for_packet(
            verifier_packet_id,
            dry_run=False,
            timeout_seconds=timeout_seconds,
            runtime_state_root=runtime_state_root,
            workdir_override=coder_result.get("worktree_path") if coder_result else None,
        )

        # Extract output from agent result
        last_message_path = result.get("last_message_path")
        if last_message_path and Path(last_message_path).exists():
            raw_output = Path(last_message_path).read_text()
        else:
            raw_output = ""

        return {"raw_output": raw_output}

    return launcher


# START_FUNCTION_CONTRACT
# Function: _create_real_reviewer_launcher
# Purpose: Create real reviewer launcher that runs live agent via codex
# Args:
#   - packet_id: Base packet identifier
#   - project: Project config with runtime_state_root
#   - timeout_seconds: Agent timeout
# Returns: Callable that launches reviewer agent and returns dict with raw_output
# Inputs: Packet ID, project config, timeout
# Side_effects: Launches live codex agent, writes to state store
# Emitted_logs: Agent execution logs
# Error_behavior: Raises exception if agent launch fails
# END_FUNCTION_CONTRACT
def _create_real_reviewer_launcher(
    packet_id: str,
    project: Any,
    timeout_seconds: int,
) -> Callable[..., dict[str, Any]]:
    """Create real reviewer launcher that runs live agent."""
    from prefect_grace.tasks.codex_launcher import _launch_codex_for_packet
    from prefect_grace.platform.state_store import PacketRegistryStore

    def launcher(**kwargs: Any) -> dict[str, Any]:
        # Create temporary reviewer packet record
        reviewer_packet_id = f"{packet_id}-REVIEWER"
        runtime_state_root = getattr(project, "runtime_state_root", None)

        # Register reviewer packet in state store
        if runtime_state_root:
            store = PacketRegistryStore(Path(runtime_state_root) / "state")
            coder_result = kwargs.get("coder_result", {})
            packet_path = kwargs.get("packet_file")

            # Create reviewer packet record
            reviewer_record = {
                "packet_id": reviewer_packet_id,
                "feature_id": packet_id.rsplit("-W", 1)[0] if "-W" in packet_id else packet_id,
                "wave_id": "W01",
                "path": str(packet_path) if packet_path else "",
                "role": "reviewer",
                "reasoning": "high",
            }
            store.upsert_packet(reviewer_record)

        # Launch reviewer agent
        result = _launch_codex_for_packet(
            reviewer_packet_id,
            dry_run=False,
            timeout_seconds=timeout_seconds,
            runtime_state_root=runtime_state_root,
            workdir_override=coder_result.get("worktree_path") if coder_result else None,
        )

        # Extract output from agent result
        last_message_path = result.get("last_message_path")
        if last_message_path and Path(last_message_path).exists():
            raw_output = Path(last_message_path).read_text()
        else:
            raw_output = ""

        return {"raw_output": raw_output}

    return launcher

# END_BLOCK: real_launchers

# START_BLOCK: status_transition_helpers

# START_FUNCTION_CONTRACT
# Function: _serialize_registry_transition
# Purpose: Convert a domain status into a JSON-safe registry transition
# Args:
#   - domain_status: Execution domain status string
# Returns: Dict with registry_status, reason, terminal flag, and failure flag
# Inputs: domain_status
# Side_effects: None (pure function)
# Emitted_logs: None
# Error_behavior: Never raises; unknown values are handled by status_model
# END_FUNCTION_CONTRACT
def _serialize_registry_transition(domain_status: str) -> dict[str, Any]:
    """Serialize the canonical registry transition for a domain status."""
    transition = apply_domain_result_to_registry(domain_status)
    return {
        "registry_status": transition.registry_status.value,
        "reason": transition.reason,
        "is_terminal": transition.is_terminal,
        "is_failure": transition.is_failure,
    }


# START_FUNCTION_CONTRACT
# Function: _registry_fields
# Purpose: Build result fields derived from the canonical registry transition
# Args:
#   - domain_status: Execution domain status string
# Returns: Dict with registry_status, registry_reason, registry_transition
# Inputs: domain_status
# Side_effects: None (pure function)
# Emitted_logs: None
# Error_behavior: Never raises; unknown values are handled by status_model
# END_FUNCTION_CONTRACT
def _registry_fields(domain_status: str) -> dict[str, Any]:
    """Build registry transition fields for E2E runner results."""
    transition = _serialize_registry_transition(domain_status)
    return {
        "registry_status": transition["registry_status"],
        "registry_reason": transition["reason"],
        "registry_transition": transition,
    }

# END_BLOCK: status_transition_helpers

# START_BLOCK: orchestrator

# START_FUNCTION_CONTRACT
# Function: run_e2e_packet
# Purpose: Run end-to-end packet execution from coder to verifier to reviewer
# Args:
#   - project_root: Project root directory
#   - packet_path: Path to EXECUTION_PACKET.md
#   - state_root: State root directory
#   - worktree_root: Worktree root directory
#   - project_key: Project identifier (default "default")
#   - attempt: Attempt number (default 1)
#   - base_ref: Git base reference (default "HEAD")
#   - dry_run: Dry-run mode (default True)
#   - execute_agent: Execute live agent (default False)
#   - fake_verifier_output: Path to fake verifier output file (default None)
#   - fake_reviewer_output: Path to fake reviewer output file (default None)
#   - timeout_seconds: Agent timeout (default 3600)
#   - keep_worktree: Preserve worktree after execution (default True)
# Returns: E2EPacketRunnerResult with domain status and execution details
# Inputs: Packet file, project config, execution flags
# Side_effects: Creates worktree, launches agent if execute_agent=True, runs handoff
# Emitted_logs: None (caller should log)
# Error_behavior: Fails closed on parse/worktree/launcher/handoff errors, returns domain status
# Behavior:
#   1. Parse and validate packet
#   2. Run managed packet runner (coder phase)
#   3. If coder passed, run verifier/reviewer handoff
#   4. Normalize domain status with priority: coder failures > handoff status
#   5. Return E2EPacketRunnerResult
# END_FUNCTION_CONTRACT
def run_e2e_packet(
    *,
    project_root: Path,
    packet_path: Path,
    state_root: Path,
    worktree_root: Path,
    project_key: str = "default",
    attempt: int = 1,
    base_ref: str = "HEAD",
    dry_run: bool = True,
    execute_agent: bool = False,
    fake_verifier_output: Path | None = None,
    fake_reviewer_output: Path | None = None,
    timeout_seconds: int = 3600,
    keep_worktree: bool = True,
) -> E2EPacketRunnerResult:
    """
    Run end-to-end packet execution flow.

    Steps:
    1. Parse and validate packet
    2. Run managed packet runner (coder phase)
    3. If coder passed, run verifier/reviewer handoff
    4. Normalize domain status
    5. Return result

    Dry-run by default, no live agents unless execute_agent=True.

    Domain status priority:
    - Coder failures (runner_error, scope_blocked, agent_failed) block handoff
    - Handoff runs only if coder passed
    - Final domain_status from handoff if coder passed, else from coder
    """
    errors: list[str] = []
    runtime_status = "started"

    # Step 1: Parse packet
    try:
        packet = parse_packet_markdown(packet_path)
        packet_id = packet.packet_id
    except Exception as e:
        domain_status = DomainStatus.RUNNER_ERROR.value
        return E2EPacketRunnerResult(
            ok=False,
            packet_id="UNKNOWN",
            attempt=attempt,
            runtime_status="failed",
            domain_status=domain_status,
            **_registry_fields(domain_status),
            worktree_path=None,
            branch_name=None,
            executor_id=None,
            managed_runner_result={},
            handoff_result=None,
            errors=[f"Failed to parse packet: {e}"],
        )

    # Step 2: Run managed packet runner (coder phase)
    try:
        # Load project config for executor selection and state store access
        from prefect_grace.platform.project_adapter import load_project_adapter
        from prefect_grace.platform.state_store import PacketRegistryStore

        try:
            project = load_project_adapter(project_root / "grace.yaml")
            # Override runtime_state_root to use the provided state_root
            project.runtime_state_root = str(state_root)
        except FileNotFoundError:
            # Fallback: create minimal project object if no config exists
            from types import SimpleNamespace
            project = SimpleNamespace(
                runtime_state_root=str(state_root),
                project_key=project_key,
                agent_executor=SimpleNamespace(
                    default="codex-cli",
                    command="codex1",
                    executors=None
                )
            )

        # Register coder packet in state store before launching
        store = PacketRegistryStore(Path(state_root) / "state")
        coder_record = {
            "packet_id": packet_id,
            "feature_id": packet_id.rsplit("-W", 1)[0] if "-W" in packet_id else packet_id,
            "wave_id": "W01",
            "path": str(packet_path),
            "role": "coder",
            "reasoning": "high",
        }
        store.upsert_packet(coder_record)

        managed_result = run_managed_packet(
            packet_file=packet_path,
            repo_root=project_root,
            worktree_root=worktree_root,
            project_key=project_key,
            packet_id=packet_id,
            attempt=attempt,
            base_ref=base_ref,
            dry_run=dry_run,
            execute_agent=execute_agent,
            timeout_seconds=timeout_seconds,
            keep_worktree=keep_worktree,
            launcher=None,  # Use default launcher
            project=project,  # Pass project for state store access
        )
    except Exception as e:
        domain_status = DomainStatus.RUNNER_ERROR.value
        return E2EPacketRunnerResult(
            ok=False,
            packet_id=packet_id,
            attempt=attempt,
            runtime_status="failed",
            domain_status=domain_status,
            **_registry_fields(domain_status),
            worktree_path=None,
            branch_name=None,
            executor_id=None,
            managed_runner_result={},
            handoff_result=None,
            errors=[f"Managed packet runner failed: {e}"],
        )

    # Step 3: Check if coder passed
    if managed_result.domain_status != DomainStatus.CHECK_PASSED.value:
        # Coder failed, handoff does not run
        runtime_status = "completed"
        domain_status = managed_result.domain_status
        return E2EPacketRunnerResult(
            ok=False,
            packet_id=packet_id,
            attempt=attempt,
            runtime_status=runtime_status,
            domain_status=domain_status,
            **_registry_fields(domain_status),
            worktree_path=managed_result.worktree_path,
            branch_name=managed_result.branch_name,
            executor_id=None,
            managed_runner_result=managed_result.to_dict(),
            handoff_result=None,
            artifact_paths=managed_result.artifact_ids,
            errors=errors if errors else ([managed_result.blocker_reason] if managed_result.blocker_reason else []),
        )

    # Step 4: Run verifier/reviewer handoff
    try:
        # Create launchers: real if no fake outputs provided, fake otherwise
        if fake_verifier_output is None and fake_reviewer_output is None:
            # Use real launchers
            verifier_launcher = _create_real_verifier_launcher(
                packet_id=packet_id,
                project=project,
                timeout_seconds=timeout_seconds,
            )
            reviewer_launcher = _create_real_reviewer_launcher(
                packet_id=packet_id,
                project=project,
                timeout_seconds=timeout_seconds,
            )
        else:
            # Use fake launchers
            verifier_launcher = _create_fake_verifier_launcher(fake_verifier_output)
            reviewer_launcher = _create_fake_reviewer_launcher(fake_reviewer_output)

        # Get packet directory
        packet_dir = packet_path.parent

        handoff_result = run_verifier_reviewer_handoff(
            packet_dir=packet_dir,
            packet_file=packet_path,
            attempt=attempt,
            coder_result=managed_result.to_dict(),
            verifier_launcher=verifier_launcher,
            reviewer_launcher=reviewer_launcher,
            project=project,  # Pass project for state store access
            dry_run=dry_run,
        )
    except Exception as e:
        runtime_status = "failed"
        domain_status = DomainStatus.HANDOFF_ERROR.value
        return E2EPacketRunnerResult(
            ok=False,
            packet_id=packet_id,
            attempt=attempt,
            runtime_status=runtime_status,
            domain_status=domain_status,
            **_registry_fields(domain_status),
            worktree_path=managed_result.worktree_path,
            branch_name=managed_result.branch_name,
            executor_id=None,
            managed_runner_result=managed_result.to_dict(),
            handoff_result=None,
            artifact_paths=managed_result.artifact_ids,
            errors=[f"Handoff failed: {e}"],
        )

    # Step 5: Normalize domain status from handoff
    runtime_status = "completed"
    domain_status = handoff_result.domain_status

    # For E2E runner, ok=True only for accepted
    # rework_required, blocked, etc. are not accepted, so ok=False
    ok = (domain_status == DomainStatus.ACCEPTED.value)

    # Collect artifact paths from both phases
    artifact_paths = list(managed_result.artifact_ids)
    if handoff_result.evidence_manifest_path:
        artifact_paths.append(handoff_result.evidence_manifest_path)
    if handoff_result.review_path:
        artifact_paths.append(handoff_result.review_path)
    if handoff_result.rework_path:
        artifact_paths.append(handoff_result.rework_path)

    # Collect errors from handoff
    if handoff_result.blocker_reason:
        errors.append(handoff_result.blocker_reason)

    return E2EPacketRunnerResult(
        ok=ok,
        packet_id=packet_id,
        attempt=attempt,
        runtime_status=runtime_status,
        domain_status=domain_status,
        **_registry_fields(domain_status),
        worktree_path=managed_result.worktree_path,
        branch_name=managed_result.branch_name,
        executor_id=None,
        managed_runner_result=managed_result.to_dict(),
        handoff_result=handoff_result.to_dict(),
        artifact_paths=artifact_paths,
        errors=errors,
    )

# END_BLOCK: orchestrator
