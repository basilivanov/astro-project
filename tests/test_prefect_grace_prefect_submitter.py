from __future__ import annotations

from types import SimpleNamespace

from prefect_grace.tasks import prefect_submitter


def test_feature_flow_parameters_builds_live_payload() -> None:
    payload = prefect_submitter.feature_flow_parameters(
        feature_id="FEAT-1",
        title="Feature 1",
        summary="Summary",
        execute=True,
        run_planner=True,
        business_context={"scope": ["one"]},
    )

    assert payload["feature_id"] == "FEAT-1"
    assert payload["dry_run"] is False
    assert payload["run_planner"] is True
    assert payload["business_context"]["scope"] == ["one"]


def test_parse_scheduled_time_normalizes_to_utc() -> None:
    parsed = prefect_submitter.parse_scheduled_time("2026-04-16T21:00:00+03:00")
    assert parsed is not None
    assert parsed.isoformat() == "2026-04-16T18:00:00+00:00"


def test_submit_feature_flow_run_creates_scheduled_prefect_run(monkeypatch) -> None:
    created: dict[str, object] = {}

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read_deployment_by_name(self, name):
            created["deployment_name"] = name
            return SimpleNamespace(id="dep-1")

        def create_flow_run_from_deployment(self, **kwargs):
            created["kwargs"] = kwargs
            return SimpleNamespace(id="flow-1", state=SimpleNamespace(name="Scheduled"))

    monkeypatch.setattr(
        prefect_submitter,
        "load_runtime_config",
        lambda: SimpleNamespace(api_url="http://127.0.0.1:4200/api", live_queue_name="grace-live"),
    )
    import sys
    from types import ModuleType

    prefect_module = ModuleType("prefect")
    prefect_client_module = ModuleType("prefect.client")
    prefect_client_orchestration_module = ModuleType("prefect.client.orchestration")
    prefect_client_orchestration_module.get_client = lambda sync_client=True: _Client()
    prefect_states_module = ModuleType("prefect.states")
    prefect_states_module.Scheduled = lambda scheduled_time=None, **kwargs: SimpleNamespace(name="Scheduled", scheduled_time=scheduled_time)
    monkeypatch.setitem(sys.modules, "prefect", prefect_module)
    monkeypatch.setitem(sys.modules, "prefect.client", prefect_client_module)
    monkeypatch.setitem(sys.modules, "prefect.client.orchestration", prefect_client_orchestration_module)
    monkeypatch.setitem(sys.modules, "prefect.states", prefect_states_module)

    result = prefect_submitter.submit_feature_flow_run(
        parameters=prefect_submitter.feature_flow_parameters(
            feature_id="FEAT-1",
            title="Feature 1",
            summary="Summary",
            execute=True,
        ),
        scheduled_for="2026-04-16T18:00:00+00:00",
        tags=["batch"],
    )

    assert result["flow_run_id"] == "flow-1"
    assert result["status"] == "Scheduled"
    assert created["deployment_name"] == prefect_submitter.FEATURE_DEPLOYMENT_NAME
    assert created["kwargs"]["work_queue_name"] == "grace-live"
    assert "prefect-native-queue" in created["kwargs"]["tags"]
    assert "batch" in created["kwargs"]["tags"]
