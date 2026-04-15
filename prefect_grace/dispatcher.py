from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

try:
    from prefect.client.orchestration import get_client
except ModuleNotFoundError:  # pragma: no cover
    get_client = None

from prefect_grace.models import FeatureStatus
from prefect_grace.runtime_config import load_runtime_config
from prefect_grace.tasks.job_queue import claim_next_job, list_jobs, update_job
from prefect_grace.tasks.state_store import find_record

FEATURE_DEPLOYMENT_NAME = "prefect-grace-feature-pipeline/live-feature-pipeline"
ACTIVE_JOB_STATUSES = {"dispatching", "submitted", "running"}


def _prefect_client_guard() -> None:
    if get_client is None:  # pragma: no cover
        raise RuntimeError("Prefect is not available in this Python environment.")


def _job_parameters(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "feature_id": job["feature_id"],
        "title": job["title"],
        "summary": job["summary"],
        "implementation_title": job["implementation_title"],
        "implementation_summary": job["implementation_summary"],
        "dry_run": not bool(job.get("execute")),
        "timeout_seconds": int(job.get("timeout_seconds") or 3600),
        "verifier_backend_profile": job.get("verifier_backend_profile"),
        "verifier_frontend_profile": job.get("verifier_frontend_profile"),
        "verifier_frontend_commands": list(job.get("verifier_frontend_commands") or []),
        "verifier_observability_profile": job.get("verifier_observability_profile"),
        "verifier_observability_commands": list(job.get("verifier_observability_commands") or []),
        "verifier_artifact_globs": list(job.get("verifier_artifact_globs") or []),
        "verifier_touches_frontend": bool(job.get("verifier_touches_frontend")),
        "verifier_requires_frontend_visual": bool(job.get("verifier_requires_frontend_visual")),
        "verifier_include_day_live_canary": bool(job.get("verifier_include_day_live_canary")),
        "prefer_agent_output": bool(job.get("prefer_agent_output", True)),
        "agent_workdir": job.get("agent_workdir"),
        "agent_sandbox": job.get("agent_sandbox"),
        "business_context": dict(job.get("business_context") or {}),
        "planner_contract": job.get("planner_contract"),
    }


def _flow_run_name(job: dict[str, Any]) -> str:
    feature_id = str(job.get("feature_id") or "unknown-feature")
    title = str(job.get("title") or "").strip()
    if title:
        return f"feature:{feature_id}:{title}"
    return f"feature:{feature_id}"


def _has_active_jobs() -> bool:
    return any(str(job.get("status") or "") in ACTIVE_JOB_STATUSES for job in list_jobs())


def _feature_domain_outcome(feature_id: str) -> tuple[str, str | None]:
    try:
        feature = find_record("features", "features", "feature_id", feature_id)
    except KeyError:
        return "completed", None

    feature_status = str(feature.get("status") or "")
    if feature_status == FeatureStatus.ACCEPTED.value:
        return "completed", feature_status
    if feature_status == FeatureStatus.BLOCKED.value:
        return "blocked", feature_status
    if feature_status == FeatureStatus.ARCHITECT_READY.value:
        return "awaiting_architect", feature_status
    if feature_status in {
        FeatureStatus.DRAFT.value,
        FeatureStatus.PLANNED.value,
        FeatureStatus.IN_PROGRESS.value,
    }:
        return "needs_rework", feature_status
    return "completed", feature_status or None


def dispatch_next_job() -> dict[str, Any] | None:
    _prefect_client_guard()
    if _has_active_jobs():
        return None

    job = claim_next_job()
    if job is None:
        return None

    runtime = load_runtime_config()
    try:
        with get_client(sync_client=True) as client:
            deployment = client.read_deployment_by_name(FEATURE_DEPLOYMENT_NAME)
            flow_run = client.create_flow_run_from_deployment(
                deployment_id=deployment.id,
                parameters=_job_parameters(job),
                name=_flow_run_name(job),
                work_queue_name=runtime.live_queue_name,
                labels={"grace.job_id": str(job["job_id"]), "grace.feature_id": str(job["feature_id"])},
                tags=["grace", "live", "queued"],
            )
    except Exception as exc:
        return update_job(
            str(job["job_id"]),
            status="failed",
            finished_at=None,
            error=f"Dispatch failed: {exc}",
        )

    return update_job(
        str(job["job_id"]),
        status="submitted",
        deployment_id=str(deployment.id),
        flow_run_id=str(flow_run.id),
        error=None,
    )


def sync_running_jobs() -> list[dict[str, Any]]:
    _prefect_client_guard()
    jobs_to_sync = [
        job
        for job in list_jobs()
        if str(job.get("status") or "") in ACTIVE_JOB_STATUSES and job.get("flow_run_id")
    ]
    results: list[dict[str, Any]] = []
    if not jobs_to_sync:
        return results

    with get_client(sync_client=True) as client:
        for job in jobs_to_sync:
            flow_run = client.read_flow_run(job["flow_run_id"])
            state_type = str(getattr(flow_run.state_type, "value", flow_run.state_type)).lower()
            state_name = str(flow_run.state_name or "").lower()
            end_time = getattr(flow_run, "end_time", None)
            updates: dict[str, Any] = {
                "prefect_state_type": state_type,
                "prefect_state_name": state_name,
            }
            if state_type in {"pending", "scheduled", "running"}:
                updates["status"] = "running"
            elif state_type == "completed":
                domain_status, feature_status = _feature_domain_outcome(str(job.get("feature_id") or ""))
                updates["status"] = domain_status
                updates["feature_status"] = feature_status
                updates["finished_at"] = end_time.isoformat() if end_time else None
                updates["error"] = None
            elif state_type in {"failed", "crashed", "cancelled"}:
                updates["status"] = "failed"
                updates["finished_at"] = end_time.isoformat() if end_time else None
                updates["error"] = f"Prefect flow run ended as {state_name}"
            else:
                updates["status"] = "running"
            results.append(update_job(str(job["job_id"]), **updates))
    return results


def run_loop(*, interval_seconds: int, once: bool = False) -> int:
    while True:
        synced = sync_running_jobs()
        dispatched = dispatch_next_job()
        print(json.dumps({"synced_jobs": len(synced), "dispatched_job": dispatched["job_id"] if dispatched else None}, ensure_ascii=False), flush=True)
        if once:
            return 0
        time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(prog="prefect-grace-dispatcher")
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    sys.exit(run_loop(interval_seconds=args.interval_seconds, once=args.once))


if __name__ == "__main__":
    main()
