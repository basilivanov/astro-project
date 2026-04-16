from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from prefect_grace.tasks.state_store import load_state, update_state


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_jobs() -> list[dict[str, Any]]:
    return list((load_state("job_queue").get("jobs") or []))


def enqueue_feature_job(
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
    brief_path: str | None = None,
) -> dict[str, Any]:
    record = {
        "job_id": f"job-{uuid.uuid4()}",
        "job_type": "feature_pipeline",
        "feature_id": feature_id,
        "title": title,
        "summary": summary,
        "implementation_title": implementation_title or "Live Implementation Packet",
        "implementation_summary": implementation_summary
        or "Execute the feature through architect, planner, coder, verifier, reviewer, and architect wave gate.",
        "execute": bool(execute),
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
        "run_planner": run_planner if run_planner is not None else None,
        "agent_workdir": agent_workdir,
        "agent_sandbox": agent_sandbox,
        "business_context": dict(business_context or {}),
        "planner_contract": dict(planner_contract or {}) if planner_contract else None,
        "brief_path": brief_path,
        "status": "queued",
        "flow_run_id": None,
        "deployment_id": None,
        "submitted_at": _now(),
        "started_at": None,
        "finished_at": None,
        "error": None,
    }

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        items = list(payload.get("jobs") or [])
        items.append(record)
        payload["jobs"] = items
        return payload

    update_state("job_queue", mutator)
    return record


def claim_next_job() -> dict[str, Any] | None:
    claimed: dict[str, Any] | None = None

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal claimed
        items = list(payload.get("jobs") or [])
        for index, item in enumerate(items):
            if str(item.get("status") or "") != "queued":
                continue
            claimed = {
                **item,
                "status": "dispatching",
                "started_at": _now(),
                "error": None,
            }
            items[index] = claimed
            payload["jobs"] = items
            return payload
        payload["jobs"] = items
        return payload

    update_state("job_queue", mutator)
    return claimed


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    updated: dict[str, Any] = {}

    def mutator(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal updated
        items = list(payload.get("jobs") or [])
        for index, item in enumerate(items):
            if str(item.get("job_id")) != job_id:
                continue
            updated = {**item, **updates}
            items[index] = updated
            payload["jobs"] = items
            return payload
        raise KeyError(f"No queued job with job_id={job_id}")

    update_state("job_queue", mutator)
    return updated
