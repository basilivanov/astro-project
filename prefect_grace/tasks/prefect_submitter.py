from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any

from prefect_grace.runtime_config import load_runtime_config

FEATURE_DEPLOYMENT_NAME = "prefect-grace-feature-pipeline/live-feature-pipeline"


def parse_scheduled_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def feature_flow_parameters(
    *,
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str | None = None,
    implementation_summary: str | None = None,
    execute: bool = False,
    timeout_seconds: int = 3600,
    verifier_backend_profile: str | None = "backend_quick",
    verifier_frontend_profile: str | None = None,
    verifier_frontend_commands: list[str] | None = None,
    verifier_observability_profile: str | None = None,
    verifier_observability_commands: list[str] | None = None,
    verifier_artifact_globs: list[str] | None = None,
    verifier_touches_frontend: bool = False,
    verifier_requires_frontend_visual: bool = False,
    verifier_include_day_live_canary: bool = False,
    prefer_agent_output: bool = True,
    run_planner: bool | None = None,
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    business_context: dict[str, Any] | None = None,
    planner_contract: dict[str, Any] | None = None,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "feature_id": feature_id,
        "title": title,
        "summary": summary,
        "implementation_title": implementation_title or "Live Implementation Packet",
        "implementation_summary": implementation_summary
        or "Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.",
        "dry_run": not bool(execute),
        "timeout_seconds": int(timeout_seconds),
        "verifier_backend_profile": verifier_backend_profile,
        "verifier_frontend_profile": verifier_frontend_profile,
        "verifier_frontend_commands": list(verifier_frontend_commands or []),
        "verifier_observability_profile": verifier_observability_profile,
        "verifier_observability_commands": list(verifier_observability_commands or []),
        "verifier_artifact_globs": list(verifier_artifact_globs or []),
        "verifier_touches_frontend": bool(verifier_touches_frontend),
        "verifier_requires_frontend_visual": bool(verifier_requires_frontend_visual),
        "verifier_include_day_live_canary": bool(verifier_include_day_live_canary),
        "prefer_agent_output": bool(prefer_agent_output),
        "run_planner": run_planner,
        "agent_workdir": agent_workdir,
        "agent_sandbox": agent_sandbox,
        "business_context": dict(business_context or {}),
        "planner_contract": dict(planner_contract or {}) if planner_contract else None,
        "commit_hash": str(commit_hash or "").strip() or None,
    }


def feature_flow_run_name(feature_id: str, title: str | None = None) -> str:
    clean_feature_id = str(feature_id or "unknown-feature")
    clean_title = str(title or "").strip()
    if clean_title:
        return f"feature:{clean_feature_id}:{clean_title}"
    return f"feature:{clean_feature_id}"


def submit_feature_flow_run(
    *,
    parameters: dict[str, Any],
    scheduled_for: str | None = None,
    tags: list[str] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    runtime = load_runtime_config()
    os.environ["PREFECT_API_URL"] = runtime.api_url
    try:
        from prefect.client.orchestration import get_client
        from prefect.states import Scheduled
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("Prefect is not available in this Python environment.") from exc

    scheduled_time = parse_scheduled_time(scheduled_for) or datetime.now(timezone.utc)
    feature_id = str(parameters.get("feature_id") or "")
    title = str(parameters.get("title") or "")
    flow_tags = ["grace", "live", f"feature:{feature_id}", "prefect-native-queue", *(tags or [])]

    with get_client(sync_client=True) as client:
        deployment = client.read_deployment_by_name(FEATURE_DEPLOYMENT_NAME)
        flow_run = client.create_flow_run_from_deployment(
            deployment_id=deployment.id,
            parameters=parameters,
            state=Scheduled(scheduled_time=scheduled_time),
            name=feature_flow_run_name(feature_id, title),
            work_queue_name=runtime.live_queue_name,
            idempotency_key=idempotency_key or f"grace-feature:{feature_id}:{scheduled_time.isoformat()}",
            labels={"grace.feature_id": feature_id},
            tags=flow_tags,
        )

    return {
        "flow_run_id": str(flow_run.id),
        "deployment_id": str(deployment.id),
        "feature_id": feature_id,
        "title": title,
        "status": str(getattr(flow_run.state, "name", None) or getattr(flow_run, "state_name", "") or "Scheduled"),
        "scheduled_for": scheduled_time.isoformat(),
        "work_queue_name": runtime.live_queue_name,
        "tags": flow_tags,
    }
