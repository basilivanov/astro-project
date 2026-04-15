from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import DeploymentUpdate
from prefect.deployments.runner import RunnerDeployment

from prefect_grace.runtime_config import load_runtime_config

ROOT_DIR = Path(__file__).resolve().parents[1]


def _prefect_cmd() -> list[str]:
    return [str(Path(sys.executable).with_name("prefect"))]


def _run(*args: str, api_url: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PREFECT_API_URL": api_url}
    return subprocess.run(
        [*_prefect_cmd(), *args],
        cwd=str(ROOT_DIR),
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


def ensure_work_pool_and_queues(*, api_url: str, work_pool_name: str, queues: list[tuple[str, int | None]]) -> None:
    _run("work-pool", "create", work_pool_name, "--type", "process", "--overwrite", api_url=api_url)
    for queue_name, limit in queues:
        inspect = _run("work-queue", "inspect", queue_name, "--pool", work_pool_name, api_url=api_url, check=False)
        if inspect.returncode != 0:
            args = ["work-queue", "create", queue_name, "--pool", work_pool_name]
            if limit is not None:
                args.extend(["--limit", str(limit)])
            _run(*args, api_url=api_url)


def _apply_deployment(
    *,
    entrypoint: str,
    deployment_name: str,
    api_url: str,
    work_pool_name: str,
    working_directory: str,
    work_queue_name: str,
    description: str,
    tags: list[str],
    concurrency_limit: int | None = None,
    interval: int | None = None,
) -> str:
    deployment = RunnerDeployment.from_entrypoint(
        entrypoint=entrypoint,
        name=deployment_name,
        work_pool_name=work_pool_name,
        work_queue_name=work_queue_name,
        description=description,
        tags=tags,
        concurrency_limit=concurrency_limit,
        interval=interval,
    )
    os.environ["PREFECT_API_URL"] = api_url
    deployment_id = str(deployment.apply(work_pool_name=work_pool_name))
    with get_client(sync_client=True) as client:
        client.update_deployment(
            deployment_id=deployment_id,
            deployment=DeploymentUpdate(
                pull_steps=[
                    {
                        "prefect.deployments.steps.set_working_directory": {
                            "directory": working_directory,
                        }
                    }
                ],
                path=None,
            ),
        )
    return deployment_id


def deploy_flows() -> dict[str, str]:
    runtime = load_runtime_config()
    deployments = {
        "feature_pipeline": _apply_deployment(
            entrypoint="prefect_grace/flows/feature_pipeline.py:feature_pipeline",
            deployment_name="live-feature-pipeline",
            api_url=runtime.api_url,
            work_pool_name=runtime.work_pool_name,
            working_directory=runtime.working_directory,
            work_queue_name=runtime.live_queue_name,
            tags=["grace", "live"],
            description="Strict GRACE feature pipeline backed by Codex packets and an LLM verifier.",
        ),
        "codex_packet": _apply_deployment(
            entrypoint="prefect_grace/flows/codex_packet.py:codex_packet_flow",
            deployment_name="live-codex-packet",
            api_url=runtime.api_url,
            work_pool_name=runtime.work_pool_name,
            working_directory=runtime.working_directory,
            work_queue_name=runtime.live_queue_name,
            tags=["grace", "ops"],
            description="Launch a single Codex packet through cliproxy.",
        ),
        "packet_transition": _apply_deployment(
            entrypoint="prefect_grace/flows/packet_lifecycle.py:packet_transition_flow",
            deployment_name="live-packet-transition",
            api_url=runtime.api_url,
            work_pool_name=runtime.work_pool_name,
            working_directory=runtime.working_directory,
            work_queue_name=runtime.monitoring_queue_name,
            tags=["grace", "ops"],
            description="Manual packet state transition helper.",
        ),
        "review_router": _apply_deployment(
            entrypoint="prefect_grace/flows/feature_pipeline.py:review_router_flow",
            deployment_name="live-review-router",
            api_url=runtime.api_url,
            work_pool_name=runtime.work_pool_name,
            working_directory=runtime.working_directory,
            work_queue_name=runtime.live_queue_name,
            tags=["grace", "ops"],
            description="Record reviewer verdicts and optionally create rework packets.",
        ),
        "live_dashboard": _apply_deployment(
            entrypoint="prefect_grace/flows/live_dashboard.py:live_dashboard_flow",
            deployment_name="live-state-dashboard",
            api_url=runtime.api_url,
            work_pool_name=runtime.work_pool_name,
            working_directory=runtime.working_directory,
            work_queue_name=runtime.monitoring_queue_name,
            interval=runtime.monitoring_interval_seconds,
            tags=["grace", "monitoring"],
            description="Publish a live GRACE dashboard artifact from file-backed state.",
        ),
    }
    return deployments


def main() -> None:
    runtime = load_runtime_config()
    os.environ["PREFECT_API_URL"] = runtime.api_url
    ensure_work_pool_and_queues(
        api_url=runtime.api_url,
        work_pool_name=runtime.work_pool_name,
        queues=[
            (runtime.live_queue_name, runtime.live_queue_limit),
            (runtime.monitoring_queue_name, runtime.monitoring_queue_limit),
        ],
    )
    deployments = deploy_flows()
    for name, deployment_id in deployments.items():
        print(f"{name}={deployment_id}")


if __name__ == "__main__":
    main()
