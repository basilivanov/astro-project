# ############################################################################
# AI_HEADER: prefect_native_submission
# ROLE: Submit ready packets as individual Prefect flow runs.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Submit ready packets to Prefect as managed packet runner flow runs.
# inputs: ProjectAdapterConfig, dry_run flag, limit, execute_agent flag, submitter callable.
# returns: NativeSubmissionResult with submission records and registry updates.
# side_effects: Updates packet registry state on successful submission.
# emitted_logs: None.
# error_behavior: Returns structured errors in result objects.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - class: PacketSubmissionRecord
#   - class: NativeSubmissionResult
#   - function: submit_ready_packets_to_prefect
# END_MODULE_MAP

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from prefect_grace.platform.backlog_controller import BacklogController
from prefect_grace.platform.state_store import PacketRegistryStore

# START_BLOCK: models


@dataclass(frozen=True)
class PacketSubmissionRecord:
    packet_id: str
    feature_id: str
    wave_id: str
    attempt: int
    source_hash: str
    idempotency_key: str
    flow_run_id: str | None
    flow_run_name: str
    deployment_name: str
    work_queue_name: str | None
    status: Literal["submitted", "dry_run", "skipped", "failed"]
    url: str | None = None
    error: str | None = None

    # START_FUNCTION_CONTRACT
    # name: to_dict
    # purpose: Serialize packet submission record to JSON-safe dict.
    # inputs:
    #   self: PacketSubmissionRecord instance.
    # returns: dict[str, Any] with all record fields.
    # side_effects: None.
    # emitted_logs: None.
    # error_behavior: None.
    # END_FUNCTION_CONTRACT
    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "feature_id": self.feature_id,
            "wave_id": self.wave_id,
            "attempt": self.attempt,
            "source_hash": self.source_hash,
            "idempotency_key": self.idempotency_key,
            "flow_run_id": self.flow_run_id,
            "flow_run_name": self.flow_run_name,
            "deployment_name": self.deployment_name,
            "work_queue_name": self.work_queue_name,
            "status": self.status,
            "url": self.url,
            "error": self.error,
        }


@dataclass(frozen=True)
class NativeSubmissionResult:
    ok: bool
    project_key: str
    dry_run: bool
    packets_planned: list[str]
    packets_submitted: list[str]
    records: list[PacketSubmissionRecord]
    blocked_packets: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]

    # START_FUNCTION_CONTRACT
    # name: to_dict
    # purpose: Serialize native submission result to JSON-safe dict.
    # inputs:
    #   self: NativeSubmissionResult instance.
    # returns: dict[str, Any] with all result fields and serialized records.
    # side_effects: None.
    # emitted_logs: None.
    # error_behavior: None.
    # END_FUNCTION_CONTRACT
    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "project_key": self.project_key,
            "dry_run": self.dry_run,
            "packets_planned": self.packets_planned,
            "packets_submitted": self.packets_submitted,
            "records": [r.to_dict() for r in self.records],
            "blocked_packets": self.blocked_packets,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# END_BLOCK: models

# START_BLOCK: submission


# START_FUNCTION_CONTRACT
# name: build_idempotency_key
# purpose: Build deterministic idempotency key for packet submission.
# inputs:
#   project_key: Project identifier.
#   packet_id: Packet identifier.
#   attempt: Attempt number.
#   source_hash: Source hash from packet registry.
# returns: Idempotency key string.
# side_effects: None.
# emitted_logs: None.
# error_behavior: None.
# END_FUNCTION_CONTRACT
def build_idempotency_key(
    project_key: str, packet_id: str, attempt: int, source_hash: str
) -> str:
    return f"grace-packet:{project_key}:{packet_id}:attempt-{attempt:04d}:{source_hash}"


# START_FUNCTION_CONTRACT
# name: submit_ready_packets_to_prefect
# purpose: Submit ready packets as individual Prefect managed packet runner flow runs.
# inputs:
#   project: ProjectAdapterConfig with project_key, repo_root, runtime_state_root.
#   dry_run: If True, plan only without calling submitter.
#   limit: Optional max number of packets to submit.
#   execute_agent: If True, submitted runs use live agent mode.
#   timeout_seconds: Timeout for managed packet runner.
#   base_ref: Git base ref for worktree creation.
#   worktree_root: Optional worktree root override.
#   scheduled_for: Optional ISO8601 scheduled time.
#   continue_on_error: If True, continue submitting after failures.
#   submitter: Optional callable for submission (for testing).
# returns: NativeSubmissionResult with submission records.
# side_effects: Updates packet registry on successful submission.
# emitted_logs: None.
# error_behavior: Returns structured errors in result.
# END_FUNCTION_CONTRACT
def submit_ready_packets_to_prefect(
    *,
    project: Any,
    dry_run: bool = True,
    limit: int | None = None,
    execute_agent: bool = False,
    timeout_seconds: int = 3600,
    base_ref: str = "HEAD",
    worktree_root: Path | None = None,
    scheduled_for: str | None = None,
    continue_on_error: bool = False,
    submitter: Callable[..., dict[str, Any]] | None = None,
) -> NativeSubmissionResult:
    project_key = project.project_key
    repo_root = Path(project.repo_root)
    runtime_state_root = Path(project.runtime_state_root)

    # Use BacklogController to get submission plan
    plan = BacklogController.plan_submission(project)

    packets_planned = plan.submission_order[:]
    if limit is not None and limit > 0:
        packets_planned = packets_planned[:limit]

    warnings = plan.warnings[:]
    errors = []
    records = []
    packets_submitted = []

    # If dry-run, return plan without submission
    if dry_run:
        for packet_id in packets_planned:
            records.append(
                PacketSubmissionRecord(
                    packet_id=packet_id,
                    feature_id="",
                    wave_id="",
                    attempt=1,
                    source_hash="",
                    idempotency_key="",
                    flow_run_id=None,
                    flow_run_name=f"packet:{packet_id}",
                    deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
                    work_queue_name=None,
                    status="dry_run",
                )
            )

        return NativeSubmissionResult(
            ok=True,
            project_key=project_key,
            dry_run=True,
            packets_planned=packets_planned,
            packets_submitted=[],
            records=records,
            blocked_packets=plan.blocked_packets,
            warnings=warnings,
            errors=errors,
        )

    # Execute mode: submit packets
    registry = PacketRegistryStore(runtime_state_root / "state")

    for packet_id in packets_planned:
        packet_record = registry.load_packet(packet_id)
        if not packet_record:
            error = {
                "code": "PACKET_NOT_FOUND_IN_REGISTRY",
                "packet_id": packet_id,
                "message": f"Packet {packet_id} not found in registry",
            }
            errors.append(error)
            records.append(
                PacketSubmissionRecord(
                    packet_id=packet_id,
                    feature_id="",
                    wave_id="",
                    attempt=1,
                    source_hash="",
                    idempotency_key="",
                    flow_run_id=None,
                    flow_run_name=f"packet:{packet_id}",
                    deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
                    work_queue_name=None,
                    status="failed",
                    error=error["message"],
                )
            )
            if not continue_on_error:
                break
            continue

        source_hash = packet_record.get("source_hash", "")
        if not source_hash:
            error = {
                "code": "MISSING_SOURCE_HASH",
                "packet_id": packet_id,
                "message": f"Packet {packet_id} missing source_hash",
            }
            errors.append(error)
            records.append(
                PacketSubmissionRecord(
                    packet_id=packet_id,
                    feature_id=packet_record.get("feature_id", ""),
                    wave_id=packet_record.get("wave_id", ""),
                    attempt=1,
                    source_hash="",
                    idempotency_key="",
                    flow_run_id=None,
                    flow_run_name=f"packet:{packet_id}",
                    deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
                    work_queue_name=None,
                    status="failed",
                    error=error["message"],
                )
            )
            if not continue_on_error:
                break
            continue

        feature_id = packet_record.get("feature_id", "")
        wave_id = packet_record.get("wave_id", "")
        title = packet_record.get("title", "")
        attempt = 1

        idempotency_key = build_idempotency_key(
            project_key, packet_id, attempt, source_hash
        )

        # Build managed packet flow parameters
        packet_path = repo_root / packet_record.get("path", "")
        wt_root = worktree_root or (runtime_state_root / "worktrees")

        parameters = {
            "packet_file": str(packet_path),
            "repo_root": str(repo_root),
            "worktree_root": str(wt_root),
            "project_key": project_key,
            "packet_id": packet_id,
            "attempt": attempt,
            "base_ref": base_ref,
            "dry_run": not execute_agent,
            "execute_agent": execute_agent,
            "timeout_seconds": timeout_seconds,
        }

        tags = [
            "grace",
            "packet",
            "managed-runner",
            f"packet:{packet_id}",
            f"feature:{feature_id}",
        ]
        if wave_id:
            tags.append(f"wave:{wave_id}")

        # Call submitter
        if submitter is None:
            error = {
                "code": "NO_SUBMITTER_PROVIDED",
                "packet_id": packet_id,
                "message": "No submitter callable provided",
            }
            errors.append(error)
            records.append(
                PacketSubmissionRecord(
                    packet_id=packet_id,
                    feature_id=feature_id,
                    wave_id=wave_id,
                    attempt=attempt,
                    source_hash=source_hash,
                    idempotency_key=idempotency_key,
                    flow_run_id=None,
                    flow_run_name=f"packet:{packet_id}:{title}" if title else f"packet:{packet_id}",
                    deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
                    work_queue_name=None,
                    status="failed",
                    error=error["message"],
                )
            )
            if not continue_on_error:
                break
            continue

        try:
            submit_result = submitter(
                parameters=parameters,
                scheduled_for=scheduled_for,
                tags=tags,
                idempotency_key=idempotency_key,
            )

            flow_run_id = submit_result.get("flow_run_id")
            flow_run_name = submit_result.get("flow_run_name", f"packet:{packet_id}")
            deployment_name = submit_result.get("deployment_name", "prefect-grace-managed-packet-runner/live-managed-packet-runner")
            work_queue_name = submit_result.get("work_queue_name")
            url = submit_result.get("url")

            # Update registry with submission info
            now = datetime.now(timezone.utc).isoformat()
            registry.upsert_packet({
                **packet_record,
                "registry_status": "submitted",
                "registry_reason": "prefect_flow_run_submitted",
                "prefect_flow_run_id": flow_run_id,
                "prefect_flow_run_name": flow_run_name,
                "prefect_deployment_name": deployment_name,
                "submission_idempotency_key": idempotency_key,
                "submitted_at": now,
            })

            records.append(
                PacketSubmissionRecord(
                    packet_id=packet_id,
                    feature_id=feature_id,
                    wave_id=wave_id,
                    attempt=attempt,
                    source_hash=source_hash,
                    idempotency_key=idempotency_key,
                    flow_run_id=flow_run_id,
                    flow_run_name=flow_run_name,
                    deployment_name=deployment_name,
                    work_queue_name=work_queue_name,
                    status="submitted",
                    url=url,
                )
            )
            packets_submitted.append(packet_id)

        except Exception as e:
            error = {
                "code": "SUBMISSION_FAILED",
                "packet_id": packet_id,
                "message": str(e),
            }
            errors.append(error)
            records.append(
                PacketSubmissionRecord(
                    packet_id=packet_id,
                    feature_id=feature_id,
                    wave_id=wave_id,
                    attempt=attempt,
                    source_hash=source_hash,
                    idempotency_key=idempotency_key,
                    flow_run_id=None,
                    flow_run_name=f"packet:{packet_id}:{title}" if title else f"packet:{packet_id}",
                    deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
                    work_queue_name=None,
                    status="failed",
                    error=str(e),
                )
            )
            if not continue_on_error:
                break

    ok = len(errors) == 0
    return NativeSubmissionResult(
        ok=ok,
        project_key=project_key,
        dry_run=False,
        packets_planned=packets_planned,
        packets_submitted=packets_submitted,
        records=records,
        blocked_packets=plan.blocked_packets,
        warnings=warnings,
        errors=errors,
    )


# END_BLOCK: submission
