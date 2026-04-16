from __future__ import annotations

from types import ModuleType, SimpleNamespace
import sys

from prefect_grace.tasks import prefect_runs


def test_list_recent_feature_flow_runs_filters_and_normalizes(monkeypatch) -> None:
    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read_flow_runs(self, **kwargs):
            return [
                SimpleNamespace(
                    id="flow-1",
                    name="feature:FEAT-1:Title",
                    parameters={"feature_id": "FEAT-1"},
                    state_type=SimpleNamespace(value="SCHEDULED"),
                    state_name="Scheduled",
                    created="created-1",
                    expected_start_time="expected-1",
                    start_time=None,
                    end_time=None,
                    work_queue_name="grace-live",
                    tags=["grace", "feature:FEAT-1"],
                ),
                SimpleNamespace(
                    id="flow-2",
                    name="dashboard:grace-live",
                    parameters={},
                    state_type=SimpleNamespace(value="COMPLETED"),
                    state_name="Completed",
                    created="created-2",
                    expected_start_time="expected-2",
                    start_time="start-2",
                    end_time="end-2",
                    work_queue_name="grace-monitoring",
                    tags=["grace"],
                ),
            ]

    monkeypatch.setattr(
        prefect_runs,
        "load_runtime_config",
        lambda: SimpleNamespace(api_url="http://127.0.0.1:4200/api"),
    )
    prefect_module = ModuleType("prefect")
    prefect_client_module = ModuleType("prefect.client")
    prefect_client_orchestration_module = ModuleType("prefect.client.orchestration")
    prefect_client_orchestration_module.get_client = lambda sync_client=True: _Client()
    prefect_client_schemas_module = ModuleType("prefect.client.schemas")
    prefect_client_schemas_sorting_module = ModuleType("prefect.client.schemas.sorting")
    prefect_client_schemas_sorting_module.FlowRunSort = SimpleNamespace(EXPECTED_START_TIME_DESC="EXPECTED_START_TIME_DESC")
    monkeypatch.setitem(sys.modules, "prefect", prefect_module)
    monkeypatch.setitem(sys.modules, "prefect.client", prefect_client_module)
    monkeypatch.setitem(sys.modules, "prefect.client.orchestration", prefect_client_orchestration_module)
    monkeypatch.setitem(sys.modules, "prefect.client.schemas", prefect_client_schemas_module)
    monkeypatch.setitem(sys.modules, "prefect.client.schemas.sorting", prefect_client_schemas_sorting_module)

    runs = prefect_runs.list_recent_feature_flow_runs(limit=10)

    assert len(runs) == 1
    assert runs[0]["flow_run_id"] == "flow-1"
    assert runs[0]["feature_id"] == "FEAT-1"
    assert runs[0]["state_type"] == "scheduled"


def test_latest_feature_run_index_picks_first_recent_run() -> None:
    index = prefect_runs.latest_feature_run_index(
        [
            {"feature_id": "FEAT-1", "flow_run_id": "flow-new"},
            {"feature_id": "FEAT-1", "flow_run_id": "flow-old"},
            {"feature_id": "FEAT-2", "flow_run_id": "flow-2"},
        ]
    )

    assert index["FEAT-1"]["flow_run_id"] == "flow-new"
    assert index["FEAT-2"]["flow_run_id"] == "flow-2"
