from __future__ import annotations

import os
from types import SimpleNamespace

from prefect_grace import dispatcher
from prefect_grace.models import FeatureStatus


class DummyClient:
    def __init__(self, state_type: str = "COMPLETED", state_name: str = "Completed"):
        self.state_type = state_type
        self.state_name = state_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read_flow_run(self, flow_run_id):
        return SimpleNamespace(
            state_type=SimpleNamespace(value=self.state_type),
            state_name=self.state_name,
            end_time=None,
        )


def test_dispatch_next_job_skips_when_active(monkeypatch):
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [{"status": "running"}])
    monkeypatch.setattr(dispatcher, "claim_next_job", lambda: (_ for _ in ()).throw(AssertionError("should not claim")))
    monkeypatch.setattr(dispatcher, "get_client", object())
    assert dispatcher.dispatch_next_job() is None


def test_feature_domain_outcome_maps_statuses(monkeypatch):
    monkeypatch.setattr(
        dispatcher,
        "find_record",
        lambda *args, **kwargs: {"status": FeatureStatus.BLOCKED.value},
    )
    assert dispatcher._feature_domain_outcome("F1") == ("blocked", FeatureStatus.BLOCKED.value)


def test_feature_domain_outcome_maps_pipeline_invalid(monkeypatch):
    monkeypatch.setattr(
        dispatcher,
        "find_record",
        lambda *args, **kwargs: {"status": FeatureStatus.PIPELINE_INVALID.value},
    )
    assert dispatcher._feature_domain_outcome("F1") == ("blocked", FeatureStatus.PIPELINE_INVALID.value)


def test_feature_domain_outcome_maps_awaiting_commit(monkeypatch):
    monkeypatch.setattr(
        dispatcher,
        "find_record",
        lambda *args, **kwargs: {"status": FeatureStatus.AWAITING_COMMIT.value},
    )
    assert dispatcher._feature_domain_outcome("F1") == ("awaiting_commit", FeatureStatus.AWAITING_COMMIT.value)


def test_sync_running_jobs_maps_completed_to_domain(monkeypatch):
    job = {"job_id": "job-1", "status": "submitted", "flow_run_id": "fr-1", "feature_id": "FEAT-1"}
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: DummyClient())
    monkeypatch.setattr(dispatcher, "find_record", lambda *args, **kwargs: {"status": FeatureStatus.ACCEPTED.value})
    updated = []
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: updated.append((job_id, updates)) or {"job_id": job_id, **updates})
    result = dispatcher.sync_running_jobs()
    assert result[0]["status"] == "accepted"
    assert updated[0][1]["feature_status"] == FeatureStatus.ACCEPTED.value


def test_sync_running_jobs_maps_completed_to_awaiting_commit(monkeypatch):
    job = {"job_id": "job-awaiting", "status": "submitted", "flow_run_id": "fr-awaiting", "feature_id": "FEAT-C"}
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: DummyClient())
    monkeypatch.setattr(dispatcher, "find_record", lambda *args, **kwargs: {"status": FeatureStatus.AWAITING_COMMIT.value})
    updated = []
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: updated.append((job_id, updates)) or {"job_id": job_id, **updates})
    result = dispatcher.sync_running_jobs()
    assert result[0]["status"] == "awaiting_commit"
    assert updated[0][1]["feature_status"] == FeatureStatus.AWAITING_COMMIT.value


def test_sync_running_jobs_maps_completed_in_progress_to_rework(monkeypatch):
    job = {"job_id": "job-2", "status": "running", "flow_run_id": "fr-2", "feature_id": "FEAT-2"}
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: DummyClient())
    monkeypatch.setattr(dispatcher, "find_record", lambda *args, **kwargs: {"status": FeatureStatus.IN_PROGRESS.value})
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: {"job_id": job_id, **updates})
    result = dispatcher.sync_running_jobs()
    assert result[0]["status"] == "rework_required"
    assert result[0]["feature_status"] == FeatureStatus.IN_PROGRESS.value


def test_dispatch_next_job_sets_prefect_api_from_runtime(monkeypatch):
    job = {
        "job_id": "job-3",
        "feature_id": "FEAT-3",
        "title": "Feature 3",
        "summary": "Summary",
        "implementation_title": "Impl",
        "implementation_summary": "Impl summary",
        "business_context": {},
    }
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [])
    monkeypatch.setattr(dispatcher, "claim_next_job", lambda: job)
    monkeypatch.setattr(
        dispatcher,
        "load_runtime_config",
        lambda: SimpleNamespace(api_url="http://127.0.0.1:4200/api", live_queue_name="grace-live"),
    )

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
            return SimpleNamespace(id="flow-1")

    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: _Client())
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: {"job_id": job_id, **updates})
    monkeypatch.delenv("PREFECT_API_URL", raising=False)

    result = dispatcher.dispatch_next_job()

    assert os.environ["PREFECT_API_URL"] == "http://127.0.0.1:4200/api"
    assert created["deployment_name"] == dispatcher.FEATURE_DEPLOYMENT_NAME
    assert result["status"] == "submitted"
    assert created["kwargs"]["parameters"]["run_planner"] is None


def test_dispatch_next_job_forwards_optional_planner_flag(monkeypatch):
    job = {
        "job_id": "job-4",
        "feature_id": "FEAT-4",
        "title": "Feature 4",
        "summary": "Summary",
        "implementation_title": "Impl",
        "implementation_summary": "Impl summary",
        "run_planner": True,
        "business_context": {},
    }
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [])
    monkeypatch.setattr(dispatcher, "claim_next_job", lambda: job)
    monkeypatch.setattr(
        dispatcher,
        "load_runtime_config",
        lambda: SimpleNamespace(api_url="http://127.0.0.1:4200/api", live_queue_name="grace-live"),
    )

    created: dict[str, object] = {}

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read_deployment_by_name(self, name):
            return SimpleNamespace(id="dep-1")

        def create_flow_run_from_deployment(self, **kwargs):
            created["kwargs"] = kwargs
            return SimpleNamespace(id="flow-4")

    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: _Client())
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: {"job_id": job_id, **updates})

    dispatcher.dispatch_next_job()

    assert created["kwargs"]["parameters"]["run_planner"] is True


def test_job_parameters_include_sequence_context(monkeypatch):
    job = {
        "job_id": "job-seq",
        "feature_id": "FEAT-SEQ",
        "title": "Feature sequence",
        "summary": "Summary",
        "implementation_title": "Impl",
        "implementation_summary": "Impl summary",
        "business_context": {"brief_path": "/tmp/brief.yaml"},
        "sequence_id": "sequence-1",
        "sequence_feature_ids": ["FEAT-SEQ", "FEAT-NEXT"],
        "sequence_position": 1,
        "sequence_total": 2,
        "status_summary_ru": "Фича 1/2: в работе.",
    }

    params = dispatcher._job_parameters(job)

    assert params["business_context"]["sequence_id"] == "sequence-1"
    assert params["business_context"]["sequence_feature_ids"] == ["FEAT-SEQ", "FEAT-NEXT"]
    assert params["business_context"]["sequence_position"] == 1
    assert params["business_context"]["sequence_total"] == 2
    assert params["business_context"]["sequence_status_summary_ru"] == "Фича 1/2: в работе."


def test_feature_domain_outcome_maps_environment_blocked(monkeypatch):
    monkeypatch.setattr(
        dispatcher,
        "find_record",
        lambda *args, **kwargs: {"status": FeatureStatus.ENVIRONMENT_BLOCKED.value},
    )
    assert dispatcher._feature_domain_outcome("F1") == ("environment_blocked", FeatureStatus.ENVIRONMENT_BLOCKED.value)
