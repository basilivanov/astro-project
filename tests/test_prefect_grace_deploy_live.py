from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace


def _import_deploy_live_with_prefect_stubs(monkeypatch):
    created: list[dict[str, object]] = []
    updated: list[dict[str, object]] = []

    class DummyDeploymentUpdate:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyRunnerDeployment:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        @classmethod
        def from_entrypoint(cls, **kwargs):
            created.append(dict(kwargs))
            return cls(**kwargs)

        def apply(self, work_pool_name: str):
            return f"dep::{self.kwargs['name']}::{work_pool_name}"

    class DummyClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update_deployment(self, deployment_id, deployment):
            updated.append({"deployment_id": deployment_id, "deployment": deployment})

    prefect_module = ModuleType("prefect")
    prefect_client_module = ModuleType("prefect.client")
    prefect_client_orchestration_module = ModuleType("prefect.client.orchestration")
    prefect_client_orchestration_module.get_client = lambda sync_client=True: DummyClient()
    prefect_client_schemas_module = ModuleType("prefect.client.schemas")
    prefect_client_schemas_actions_module = ModuleType("prefect.client.schemas.actions")
    prefect_client_schemas_actions_module.DeploymentUpdate = DummyDeploymentUpdate
    prefect_deployments_module = ModuleType("prefect.deployments")
    prefect_deployments_runner_module = ModuleType("prefect.deployments.runner")
    prefect_deployments_runner_module.RunnerDeployment = DummyRunnerDeployment

    monkeypatch.setitem(sys.modules, "prefect", prefect_module)
    monkeypatch.setitem(sys.modules, "prefect.client", prefect_client_module)
    monkeypatch.setitem(sys.modules, "prefect.client.orchestration", prefect_client_orchestration_module)
    monkeypatch.setitem(sys.modules, "prefect.client.schemas", prefect_client_schemas_module)
    monkeypatch.setitem(sys.modules, "prefect.client.schemas.actions", prefect_client_schemas_actions_module)
    monkeypatch.setitem(sys.modules, "prefect.deployments", prefect_deployments_module)
    monkeypatch.setitem(sys.modules, "prefect.deployments.runner", prefect_deployments_runner_module)

    sys.modules.pop("prefect_grace.deploy_live", None)
    deploy_live = importlib.import_module("prefect_grace.deploy_live")
    deploy_live = importlib.reload(deploy_live)
    return deploy_live, created, updated


def test_deploy_flows_excludes_extra_packet_deployment(monkeypatch):
    deploy_live, created, updated = _import_deploy_live_with_prefect_stubs(monkeypatch)
    monkeypatch.setattr(
        deploy_live,
        "load_runtime_config",
        lambda: SimpleNamespace(
            api_url="http://127.0.0.1:4200/api",
            work_pool_name="astro-process",
            working_directory="/opt/astro-project",
            live_queue_name="grace-live",
            live_queue_limit=1,
            monitoring_queue_name="grace-monitoring",
            monitoring_interval_seconds=300,
        ),
    )

    deployments = deploy_live.deploy_flows()

    assert set(deployments) == {
        "feature_pipeline",
        "packet_transition",
        "review_router",
        "live_dashboard",
    }
    assert [item["name"] for item in created] == [
        "live-feature-pipeline",
        "live-packet-transition",
        "live-review-router",
        "live-state-dashboard",
    ]
    assert created[0]["concurrency_limit"] == 1
    assert all("codex" not in str(item["name"]) for item in created)
    assert len(updated) == 4


def test_ensure_work_pool_and_queues_updates_existing_limits(monkeypatch):
    deploy_live, _, _ = _import_deploy_live_with_prefect_stubs(monkeypatch)
    calls: list[tuple[str, ...]] = []

    def _fake_run(*args, api_url: str, check: bool = True):
        calls.append(tuple(args))
        if args[:2] == ("work-queue", "inspect"):
            return SimpleNamespace(returncode=0)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(deploy_live, "_run", _fake_run)

    deploy_live.ensure_work_pool_and_queues(
        api_url="http://127.0.0.1:4200/api",
        work_pool_name="astro-process",
        queues=[("grace-live", 1), ("grace-monitoring", None)],
    )

    assert ("work-queue", "set-concurrency-limit", "grace-live", "1", "--pool", "astro-process") in calls
    assert ("work-queue", "clear-concurrency-limit", "grace-monitoring", "--pool", "astro-process") in calls


def test_main_prints_only_canonical_deployments(monkeypatch, capsys):
    deploy_live, _, _ = _import_deploy_live_with_prefect_stubs(monkeypatch)
    monkeypatch.setattr(
        deploy_live,
        "load_runtime_config",
        lambda: SimpleNamespace(
            api_url="http://127.0.0.1:4200/api",
            work_pool_name="astro-process",
            live_queue_name="grace-live",
            live_queue_limit=1,
            monitoring_queue_name="grace-monitoring",
            monitoring_queue_limit=1,
        ),
    )

    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        deploy_live,
        "ensure_work_pool_and_queues",
        lambda **kwargs: calls.append(kwargs),
    )
    monkeypatch.setattr(
        deploy_live,
        "deploy_flows",
        lambda: {
            "feature_pipeline": "dep-feature",
            "packet_transition": "dep-transition",
            "review_router": "dep-review",
            "live_dashboard": "dep-dashboard",
        },
    )

    deploy_live.main()

    assert calls == [
        {
            "api_url": "http://127.0.0.1:4200/api",
            "work_pool_name": "astro-process",
            "queues": [("grace-live", 1), ("grace-monitoring", 1)],
        }
    ]
    assert capsys.readouterr().out.strip().splitlines() == [
        "feature_pipeline=dep-feature",
        "packet_transition=dep-transition",
        "review_router=dep-review",
        "live_dashboard=dep-dashboard",
    ]
