"""
# ============================================================================
# AI_HEADER: GRACE Prefect Worker Binding Module
# ============================================================================
#
# This module provides a guarded Prefect binding layer that proves the
# portable GRACE orchestrator is connected to the real Prefect stack before
# any live packet is submitted.
#
# Key Concepts:
# - Fail-closed by default (no Prefect imports at module load time)
# - Dry-run by default (no mutations without explicit approval)
# - Validates routing contract (work pool, queues, deployment)
# - Bounded worker runtime smoke (no persistent workers)
# - Zero flow runs created in dry-run or apply mode
#
# Module Dependencies:
# - prefect (lazy import)
# - prefect_grace.runtime_config
# - No automatic mutations
#
# ============================================================================
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# START_MODULE_CONTRACT
# Module: prefect_worker_binding
# Purpose: Validate Prefect infrastructure readiness for live packet execution
# Exports: PrefectWorkerBindingResult, run_prefect_worker_binding_preflight
# Dependencies: prefect (lazy), runtime_config
# Constraints: Fail-closed, dry-run by default, no mutations without approval
# END_MODULE_CONTRACT

# START_MODULE_MAP
# Block: models - PrefectWorkerBindingResult dataclass
# Block: preflight - run_prefect_worker_binding_preflight function
# Block: validation - Prefect infrastructure validation helpers
# END_MODULE_MAP

# START_BLOCK: models

@dataclass(frozen=True)
class PrefectWorkerBindingResult:
    """Result of Prefect worker binding preflight check.

    Fields:
    - ok: True if all infrastructure is ready for live packet
    - project_key: Project identifier
    - mode: Operation mode (prefect_worker_binding)
    - dry_run: Whether this was a dry-run
    - prefect_api_url: Prefect API URL
    - prefect_version: Prefect version or None if unavailable
    - server_healthy: Whether Prefect server is reachable
    - work_pool_name: Expected work pool name
    - work_pool_status: Work pool status or None if not found
    - work_pool_type: Work pool type or None if not found
    - required_queues: List of required queue names
    - queue_statuses: Dict of queue name to status info
    - deployment_name: Expected deployment name
    - deployment_exists: Whether deployment exists
    - deployment_work_pool_name: Deployment's work pool or None
    - deployment_work_queue_name: Deployment's work queue or None
    - deployment_parameters_valid: Whether deployment parameters match expected
    - worker_runtime_smoke: Worker runtime smoke test results
    - deployment_mutation: Mutation status (none, dry_run_would_register, applied)
    - prefect_runs_created: Count of Prefect flow runs created
    - live_agents_started: Count of live agents started
    - warnings: List of warning messages
    - errors: List of error dicts with type and message
    """
    ok: bool
    project_key: str
    mode: str
    dry_run: bool
    prefect_api_url: str
    prefect_version: str | None
    server_healthy: bool
    work_pool_name: str
    work_pool_status: str | None
    work_pool_type: str | None
    required_queues: list[str]
    queue_statuses: dict[str, dict[str, Any]]
    deployment_name: str
    deployment_exists: bool
    deployment_work_pool_name: str | None
    deployment_work_queue_name: str | None
    deployment_parameters_valid: bool
    worker_runtime_smoke: dict[str, Any]
    deployment_mutation: str
    prefect_runs_created: int
    live_agents_started: int
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    # START_FUNCTION_CONTRACT
    # Function: to_dict
    # Purpose: Serialize PrefectWorkerBindingResult to dict for JSON output
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
            "project_key": self.project_key,
            "mode": self.mode,
            "dry_run": self.dry_run,
            "prefect_api_url": self.prefect_api_url,
            "prefect_version": self.prefect_version,
            "server_healthy": self.server_healthy,
            "work_pool_name": self.work_pool_name,
            "work_pool_status": self.work_pool_status,
            "work_pool_type": self.work_pool_type,
            "required_queues": list(self.required_queues),
            "queue_statuses": dict(self.queue_statuses),
            "deployment_name": self.deployment_name,
            "deployment_exists": self.deployment_exists,
            "deployment_work_pool_name": self.deployment_work_pool_name,
            "deployment_work_queue_name": self.deployment_work_queue_name,
            "deployment_parameters_valid": self.deployment_parameters_valid,
            "worker_runtime_smoke": dict(self.worker_runtime_smoke),
            "deployment_mutation": self.deployment_mutation,
            "prefect_runs_created": self.prefect_runs_created,
            "live_agents_started": self.live_agents_started,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

# END_BLOCK: models

# START_BLOCK: validation

def _check_prefect_available() -> tuple[bool, str | None, list[dict[str, Any]]]:
    """Check if Prefect is available and return version.

    Note: This function is only used when no client is injected.
    In production, callers should inject a client from runtime_adapter.py.
    """
    # Since only runtime_adapter.py can import prefect, we return unavailable
    # when no client is injected. Callers should use runtime_adapter to create clients.
    return False, None, [{"type": "PREFECT_UNAVAILABLE", "message": "Prefect client must be injected (use runtime_adapter.py to create clients)"}]


def _check_server_health(prefect_client: Any, api_url: str) -> tuple[bool, list[dict[str, Any]]]:
    """Check if Prefect server is healthy."""
    try:
        # Try to get server version as health check
        prefect_client.api_healthcheck()
        return True, []
    except Exception as e:
        return False, [{"type": "PREFECT_API_UNREACHABLE", "message": f"Cannot reach Prefect API at {api_url}: {e}"}]


def _check_work_pool(prefect_client: Any, work_pool_name: str) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """Check work pool exists and is ready."""
    try:
        work_pool = prefect_client.read_work_pool(work_pool_name)

        if not work_pool:
            return None, None, [{"type": "WORK_POOL_NOT_FOUND", "message": f"Work pool '{work_pool_name}' not found"}]

        pool_type = getattr(work_pool, "type", None)
        if pool_type != "process":
            return None, pool_type, [{"type": "WORK_POOL_WRONG_TYPE", "message": f"Work pool type is '{pool_type}', expected 'process'"}]

        is_paused = getattr(work_pool, "is_paused", False)
        if is_paused:
            return "PAUSED", pool_type, [{"type": "WORK_POOL_PAUSED", "message": f"Work pool '{work_pool_name}' is paused"}]

        return "READY", pool_type, []
    except Exception as e:
        return None, None, [{"type": "WORK_POOL_CHECK_FAILED", "message": f"Failed to check work pool: {e}"}]


def _check_queues(prefect_client: Any, work_pool_name: str, required_queues: list[str]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Check required queues exist and are ready."""
    queue_statuses = {}
    errors = []

    for queue_name in required_queues:
        try:
            queue = prefect_client.read_work_queue_by_name(queue_name, work_pool_name)

            if not queue:
                queue_statuses[queue_name] = {"exists": False, "status": None}
                errors.append({"type": "QUEUE_NOT_FOUND", "message": f"Queue '{queue_name}' not found in work pool '{work_pool_name}'"})
            else:
                is_paused = getattr(queue, "is_paused", False)
                status = "PAUSED" if is_paused else "READY"
                queue_statuses[queue_name] = {"exists": True, "status": status}

                if is_paused:
                    errors.append({"type": "QUEUE_PAUSED", "message": f"Queue '{queue_name}' is paused"})
        except Exception as e:
            queue_statuses[queue_name] = {"exists": False, "status": None}
            errors.append({"type": "QUEUE_CHECK_FAILED", "message": f"Failed to check queue '{queue_name}': {e}"})

    return queue_statuses, errors

# END_BLOCK: validation

# START_BLOCK: deployment_apply

def _apply_managed_packet_deployment(prefect_client: Any, api_url: str, work_pool_name: str, work_queue_name: str) -> tuple[bool, str | None, list[dict[str, Any]]]:
    """Apply the managed packet runner deployment.

    Delegates to runtime_adapter since it requires prefect imports.
    Returns (success, deployment_id, errors).
    """
    try:
        from prefect_grace.platform.runtime_adapter import apply_managed_packet_deployment_helper
        return apply_managed_packet_deployment_helper(prefect_client, api_url, work_pool_name, work_queue_name)
    except Exception as e:
        return False, None, [{"type": "DEPLOYMENT_APPLY_FAILED", "message": f"Failed to apply deployment: {e}"}]

# END_BLOCK: deployment_apply

# START_BLOCK: worker_smoke

def _run_worker_smoke_test(prefect_client: Any, work_pool_name: str, work_queue_name: str) -> dict[str, Any]:
    """Run worker runtime smoke test.

    Returns dict with smoke_ran, ok, and optional error fields.
    """
    try:
        # For now, just verify we can read the work pool and queue
        # A full smoke test would start a worker process and verify it can pick up work
        # But that's beyond the scope of a preflight check

        work_pool = prefect_client.read_work_pool(work_pool_name)
        if not work_pool:
            return {"smoke_ran": True, "ok": False, "error": "Work pool not found"}

        queue = prefect_client.read_work_queue_by_name(work_queue_name, work_pool_name)
        if not queue:
            return {"smoke_ran": True, "ok": False, "error": "Work queue not found"}

        # Basic smoke passed: infrastructure is readable
        return {"smoke_ran": True, "ok": True}

    except Exception as e:
        return {"smoke_ran": True, "ok": False, "error": f"Smoke test failed: {e}"}

# END_BLOCK: worker_smoke

# START_BLOCK: deployment_validation

def _check_deployment(prefect_client: Any, deployment_name: str, expected_work_pool: str, expected_queue: str) -> tuple[bool, str | None, str | None, bool, list[dict[str, Any]]]:
    """Check deployment exists and has correct routing."""
    try:
        # Parse deployment name (format: flow_name/deployment_name)
        parts = deployment_name.split("/")
        if len(parts) != 2:
            return False, None, None, False, [{"type": "DEPLOYMENT_NAME_INVALID", "message": f"Invalid deployment name format: {deployment_name}"}]

        flow_name, dep_name = parts

        # Try to read deployment
        try:
            deployment = prefect_client.read_deployment_by_name(deployment_name)
        except Exception:
            deployment = None

        if not deployment:
            return False, None, None, False, [{"type": "DEPLOYMENT_NOT_FOUND", "message": f"Deployment '{deployment_name}' not found"}]

        # Check work pool
        dep_work_pool = getattr(deployment, "work_pool_name", None)
        dep_work_queue = getattr(deployment, "work_queue_name", None)

        errors = []
        parameters_valid = True

        if dep_work_pool != expected_work_pool:
            errors.append({"type": "DEPLOYMENT_WRONG_WORK_POOL", "message": f"Deployment work pool is '{dep_work_pool}', expected '{expected_work_pool}'"})
            parameters_valid = False

        if dep_work_queue != expected_queue:
            errors.append({"type": "DEPLOYMENT_WRONG_QUEUE", "message": f"Deployment work queue is '{dep_work_queue}', expected '{expected_queue}'"})
            parameters_valid = False

        return True, dep_work_pool, dep_work_queue, parameters_valid, errors

    except Exception as e:
        return False, None, None, False, [{"type": "DEPLOYMENT_CHECK_FAILED", "message": f"Failed to check deployment: {e}"}]

# END_BLOCK: deployment_validation

# START_BLOCK: preflight

# START_FUNCTION_CONTRACT
# Function: run_prefect_worker_binding_preflight
# Purpose: Validate Prefect infrastructure readiness for live packet execution
# Args:
#   - project_config: Path to grace.yaml project config
#   - dry_run: Dry-run mode (default True)
#   - apply_deployment: Apply deployment registration (requires approval)
#   - acknowledge_prefect_mutation: Acknowledge Prefect mutation flag
#   - approval_token: Approval token for deployment mutation
#   - run_worker_smoke: Run worker runtime smoke test
#   - prefect_client: Injected Prefect client for testing
# Returns: PrefectWorkerBindingResult with validation results
# Inputs: Project config path, execution flags, optional injected client
# Side_effects: Reads Prefect API if client not injected, may apply deployment if approved
# Emitted_logs: None (caller should log)
# Error_behavior: Fails closed on any validation error, returns ok=False
# END_FUNCTION_CONTRACT
def run_prefect_worker_binding_preflight(
    *,
    project_config: Path,
    dry_run: bool = True,
    apply_deployment: bool = False,
    acknowledge_prefect_mutation: bool = False,
    approval_token: str | None = None,
    run_worker_smoke: bool = False,
    prefect_client: Any | None = None,
) -> PrefectWorkerBindingResult:
    """
    Run Prefect worker binding preflight check.

    Validates that Prefect infrastructure is ready for live packet execution:
    - Prefect server is healthy
    - Work pool exists and is ready
    - Required queues exist and are ready
    - Deployment exists and has correct routing

    Args:
        project_config: Path to grace.yaml project config
        dry_run: Dry-run mode (default True)
        apply_deployment: Apply deployment registration (requires approval)
        acknowledge_prefect_mutation: Acknowledge Prefect mutation flag
        approval_token: Approval token for deployment mutation
        run_worker_smoke: Run worker runtime smoke test
        prefect_client: Injected Prefect client for testing

    Returns:
        PrefectWorkerBindingResult with validation results
    """
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []

    # Load project config
    try:
        from prefect_grace.platform.project_adapter import load_project_adapter
        project = load_project_adapter(project_config)
        project_key = getattr(project, "project_key", "default")
    except Exception as e:
        return PrefectWorkerBindingResult(
            ok=False,
            project_key="unknown",
            mode="prefect_worker_binding",
            dry_run=dry_run,
            prefect_api_url="",
            prefect_version=None,
            server_healthy=False,
            work_pool_name="",
            work_pool_status=None,
            work_pool_type=None,
            required_queues=[],
            queue_statuses={},
            deployment_name="",
            deployment_exists=False,
            deployment_work_pool_name=None,
            deployment_work_queue_name=None,
            deployment_parameters_valid=False,
            worker_runtime_smoke={},
            deployment_mutation="none",
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[{"type": "PROJECT_CONFIG_LOAD_FAILED", "message": f"Failed to load project config: {e}"}],
        )

    # __CONTINUE_HERE__

    # Get runtime config
    try:
        from prefect_grace.runtime_config import load_runtime_config
        runtime_config = load_runtime_config()
        api_url = runtime_config.api_url
        work_pool_name = runtime_config.work_pool_name
    except Exception as e:
        api_url = ""
        work_pool_name = "astro-process"
        warnings.append(f"Failed to load runtime config: {e}")

    # Required queues
    required_queues = ["grace-live", "grace-monitoring"]

    # Expected deployment name
    from prefect_grace.tasks.prefect_submitter import MANAGED_PACKET_DEPLOYMENT_NAME
    deployment_name = MANAGED_PACKET_DEPLOYMENT_NAME

    # Check Prefect availability
    if prefect_client is None:
        # No client injected - fail closed
        # In production, callers should inject a client created via runtime_adapter.py
        return PrefectWorkerBindingResult(
            ok=False,
            project_key=project_key,
            mode="prefect_worker_binding",
            dry_run=dry_run,
            prefect_api_url=api_url,
            prefect_version=None,
            server_healthy=False,
            work_pool_name=work_pool_name,
            work_pool_status=None,
            work_pool_type=None,
            required_queues=required_queues,
            queue_statuses={},
            deployment_name=deployment_name,
            deployment_exists=False,
            deployment_work_pool_name=None,
            deployment_work_queue_name=None,
            deployment_parameters_valid=False,
            worker_runtime_smoke={},
            deployment_mutation="none",
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[{"type": "PREFECT_CLIENT_REQUIRED", "message": "Prefect client must be injected (no client provided)"}],
        )
    else:
        prefect_version = "injected"

    # Check server health
    server_healthy, health_errors = _check_server_health(prefect_client, api_url)
    errors.extend(health_errors)

    if not server_healthy:
        return PrefectWorkerBindingResult(
            ok=False,
            project_key=project_key,
            mode="prefect_worker_binding",
            dry_run=dry_run,
            prefect_api_url=api_url,
            prefect_version=prefect_version,
            server_healthy=False,
            work_pool_name=work_pool_name,
            work_pool_status=None,
            work_pool_type=None,
            required_queues=required_queues,
            queue_statuses={},
            deployment_name=deployment_name,
            deployment_exists=False,
            deployment_work_pool_name=None,
            deployment_work_queue_name=None,
            deployment_parameters_valid=False,
            worker_runtime_smoke={},
            deployment_mutation="none",
            prefect_runs_created=0,
            live_agents_started=0,
            errors=errors,
        )

    # __CONTINUE_HERE__

    # Check work pool
    work_pool_status, work_pool_type, pool_errors = _check_work_pool(prefect_client, work_pool_name)
    errors.extend(pool_errors)

    # Check queues
    queue_statuses, queue_errors = _check_queues(prefect_client, work_pool_name, required_queues)
    errors.extend(queue_errors)

    # Check deployment
    deployment_exists, dep_work_pool, dep_work_queue, parameters_valid, dep_errors = _check_deployment(
        prefect_client, deployment_name, work_pool_name, "grace-live"
    )
    errors.extend(dep_errors)

    # Determine deployment mutation status
    deployment_mutation = "none"
    if apply_deployment:
        if not acknowledge_prefect_mutation:
            errors.append({"type": "DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED", "message": "Deployment apply requires --i-understand-prefect-mutation flag"})
        elif approval_token != "deployment":
            errors.append({"type": "DEPLOYMENT_APPLY_NOT_APPROVED", "message": "Deployment apply requires GRACE_PREFECT_BINDING_APPROVED=deployment"})
        elif dry_run:
            # Dry-run mode: report what would happen
            deployment_mutation = "dry_run_would_apply"
        else:
            # Live mode: actually apply deployment
            apply_success, deployment_id, apply_errors = _apply_managed_packet_deployment(
                prefect_client, api_url, work_pool_name, "grace-live"
            )
            if apply_success:
                deployment_mutation = "applied"
                warnings.append(f"Deployment applied: {deployment_id}")
            else:
                deployment_mutation = "apply_failed"
                errors.extend(apply_errors)
    elif not deployment_exists:
        deployment_mutation = "dry_run_would_register"

    # Worker runtime smoke
    worker_runtime_smoke = {"smoke_ran": False, "ok": None}
    if run_worker_smoke:
        worker_runtime_smoke = _run_worker_smoke_test(prefect_client, work_pool_name, "grace-live")
        if not worker_runtime_smoke["ok"]:
            errors.append({"type": "WORKER_SMOKE_FAILED", "message": worker_runtime_smoke.get("error", "Worker smoke test failed")})

    # Determine overall ok status
    ok = (
        server_healthy
        and work_pool_status == "READY"
        and work_pool_type == "process"
        and all(q["exists"] and q["status"] == "READY" for q in queue_statuses.values())
        and (deployment_exists and parameters_valid)
        and len([e for e in errors if e["type"] not in ["DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED", "DEPLOYMENT_APPLY_NOT_APPROVED"]]) == 0
    )

    return PrefectWorkerBindingResult(
        ok=ok,
        project_key=project_key,
        mode="prefect_worker_binding",
        dry_run=dry_run,
        prefect_api_url=api_url,
        prefect_version=prefect_version,
        server_healthy=server_healthy,
        work_pool_name=work_pool_name,
        work_pool_status=work_pool_status,
        work_pool_type=work_pool_type,
        required_queues=required_queues,
        queue_statuses=queue_statuses,
        deployment_name=deployment_name,
        deployment_exists=deployment_exists,
        deployment_work_pool_name=dep_work_pool,
        deployment_work_queue_name=dep_work_queue,
        deployment_parameters_valid=parameters_valid,
        worker_runtime_smoke=worker_runtime_smoke,
        deployment_mutation=deployment_mutation,
        prefect_runs_created=0,
        live_agents_started=0,
        warnings=warnings,
        errors=errors,
    )

# END_BLOCK: preflight



