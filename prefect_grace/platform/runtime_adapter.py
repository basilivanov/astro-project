# ############################################################################
# AI_HEADER: runtime_adapter
# ROLE: Abstract runtime interface for workflow execution (Prefect, dry-run, etc).
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Provide pluggable runtime adapters for submitting packet runs.
# inputs: Packet data, runtime parameters, execution mode.
# returns: Run references, status, artifacts.
# side_effects: May create Prefect flow runs if PrefectRuntimeAdapter is used.
# emitted_logs: None.
# error_behavior: Returns structured errors for runtime failures.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - class: WorkflowRuntime
#   - class: DryRunRuntime
#   - class: PrefectRuntimeAdapter
#   - function: create_runtime
# END_MODULE_MAP

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# START_BLOCK: runtime_interface

@dataclass
class WorkflowRuntime(ABC):
    name: str

    # START_FUNCTION_CONTRACT
    # name: submit_packet_run
    # purpose: Submit a packet for execution in the workflow runtime.
    # inputs:
    #   packet: dict containing packet metadata.
    #   parameters: dict of runtime parameters.
    # returns: dict with run reference (run_id, url, etc).
    # side_effects: May create external workflow runs.
    # emitted_logs: None.
    # error_behavior: Raises RuntimeError on submission failure.
    # END_FUNCTION_CONTRACT
    @abstractmethod
    def submit_packet_run(self, packet: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        pass

    # START_FUNCTION_CONTRACT
    # name: publish_artifact
    # purpose: Publish an artifact to the runtime.
    # inputs:
    #   run_ref: dict with run reference.
    #   name: artifact name.
    #   body: artifact content (string or dict).
    # returns: None.
    # side_effects: May write artifacts to external storage.
    # emitted_logs: None.
    # error_behavior: Raises RuntimeError on publish failure.
    # END_FUNCTION_CONTRACT
    @abstractmethod
    def publish_artifact(self, run_ref: dict[str, Any], name: str, body: str | dict) -> None:
        pass

    # START_FUNCTION_CONTRACT
    # name: read_run_status
    # purpose: Read current status of a workflow run.
    # inputs:
    #   run_ref: dict with run reference.
    # returns: dict with status, state, timestamps.
    # side_effects: May query external runtime API.
    # emitted_logs: None.
    # error_behavior: Returns error dict if run not found.
    # END_FUNCTION_CONTRACT
    @abstractmethod
    def read_run_status(self, run_ref: dict[str, Any]) -> dict[str, Any]:
        pass

# END_BLOCK: runtime_interface

# START_BLOCK: dry_run_runtime

class DryRunRuntime(WorkflowRuntime):
    def __init__(self):
        super().__init__(name="dry-run")
        self.submitted_runs: list[dict[str, Any]] = []
        self.artifacts: list[dict[str, Any]] = []

    def submit_packet_run(self, packet: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        run_id = f"dry-run-{uuid.uuid4().hex[:8]}"
        run_ref = {
            "run_id": run_id,
            "runtime": "dry-run",
            "packet_id": packet.get("packet_id"),
            "parameters": parameters,
            "url": f"dry-run://localhost/{run_id}",
        }
        self.submitted_runs.append(run_ref)
        return run_ref

    def publish_artifact(self, run_ref: dict[str, Any], name: str, body: str | dict) -> None:
        artifact = {
            "run_id": run_ref.get("run_id"),
            "name": name,
            "body": body,
        }
        self.artifacts.append(artifact)

    def read_run_status(self, run_ref: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": run_ref.get("run_id"),
            "state": "DRY_RUN",
            "status": "simulated",
        }

# END_BLOCK: dry_run_runtime

# START_BLOCK: prefect_runtime_adapter

class PrefectRuntimeAdapter(WorkflowRuntime):
    def __init__(self, work_pool: str | None = None, queue: str | None = None):
        super().__init__(name="prefect")
        self.work_pool = work_pool
        self.queue = queue

    def submit_packet_run(self, packet: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            from prefect_grace.tasks.prefect_submitter import submit_feature_flow_run
        except ImportError as e:
            raise RuntimeError(f"Prefect runtime unavailable: {e}")

        packet_id = packet.get("packet_id")
        feature_id = packet.get("feature_id")

        if not packet_id or not feature_id:
            raise ValueError("packet_id and feature_id are required")

        flow_run = submit_feature_flow_run(
            feature_id=feature_id,
            parameters=parameters,
            work_pool=self.work_pool,
            queue=self.queue,
        )

        return {
            "run_id": flow_run.id,
            "runtime": "prefect",
            "packet_id": packet_id,
            "feature_id": feature_id,
            "url": f"/flow-runs/flow-run/{flow_run.id}",
            "state": flow_run.state.name if flow_run.state else "UNKNOWN",
        }

    def publish_artifact(self, run_ref: dict[str, Any], name: str, body: str | dict) -> None:
        try:
            from prefect.artifacts import create_markdown_artifact
            import json
        except ImportError as e:
            raise RuntimeError(f"Prefect artifacts unavailable: {e}")

        if isinstance(body, dict):
            import json as json_module
            content = f"```json\n{json_module.dumps(body, indent=2)}\n```"
        else:
            content = body

        create_markdown_artifact(
            key=name,
            markdown=content,
            description=f"Artifact for run {run_ref.get('run_id')}",
        )

    def read_run_status(self, run_ref: dict[str, Any]) -> dict[str, Any]:
        run_id = run_ref.get("run_id")
        if not run_id:
            return {"error": "run_id missing"}

        try:
            from prefect.client.orchestration import get_client
        except ImportError as e:
            raise RuntimeError(f"Prefect client unavailable: {e}")

        async def _fetch():
            async with get_client() as client:
                flow_run = await client.read_flow_run(run_id)
                return {
                    "run_id": str(flow_run.id),
                    "state": flow_run.state.name if flow_run.state else "UNKNOWN",
                    "status": flow_run.state.type.value if flow_run.state else "UNKNOWN",
                }

        try:
            import asyncio
            return asyncio.run(_fetch())
        except Exception as e:
            return {"error": str(e)}

# END_BLOCK: prefect_runtime_adapter

# START_BLOCK: factory

# START_FUNCTION_CONTRACT
# name: create_runtime
# purpose: Factory function to create runtime adapter instances.
# inputs:
#   runtime_type: string identifier (dry-run, prefect).
#   config: optional dict with runtime-specific configuration.
# returns: WorkflowRuntime instance.
# side_effects: None.
# emitted_logs: None.
# error_behavior: Raises ValueError for unknown runtime types.
# END_FUNCTION_CONTRACT
def create_runtime(runtime_type: str, config: dict[str, Any] | None = None) -> WorkflowRuntime:
    config = config or {}

    if runtime_type == "dry-run":
        return DryRunRuntime()
    elif runtime_type == "prefect":
        return PrefectRuntimeAdapter(
            work_pool=config.get("work_pool"),
            queue=config.get("queue"),
        )
    else:
        raise ValueError(f"Unknown runtime type: {runtime_type}")

# END_BLOCK: factory
