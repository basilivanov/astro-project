from __future__ import annotations

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


def test_sync_running_jobs_maps_completed_to_domain(monkeypatch):
    job = {"job_id": "job-1", "status": "submitted", "flow_run_id": "fr-1", "feature_id": "FEAT-1"}
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: DummyClient())
    monkeypatch.setattr(dispatcher, "find_record", lambda *args, **kwargs: {"status": FeatureStatus.ACCEPTED.value})
    updated = []
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: updated.append((job_id, updates)) or {"job_id": job_id, **updates})
    result = dispatcher.sync_running_jobs()
    assert result[0]["status"] == "completed"
    assert updated[0][1]["feature_status"] == FeatureStatus.ACCEPTED.value


def test_sync_running_jobs_maps_completed_in_progress_to_rework(monkeypatch):
    job = {"job_id": "job-2", "status": "running", "flow_run_id": "fr-2", "feature_id": "FEAT-2"}
    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: DummyClient())
    monkeypatch.setattr(dispatcher, "find_record", lambda *args, **kwargs: {"status": FeatureStatus.IN_PROGRESS.value})
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: {"job_id": job_id, **updates})
    result = dispatcher.sync_running_jobs()
    assert result[0]["status"] == "needs_rework"
    assert result[0]["feature_status"] == FeatureStatus.IN_PROGRESS.value
