from __future__ import annotations

from types import SimpleNamespace

from prefect_grace import dispatcher
from prefect_grace.models import FeatureStatus


class _CompletedClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read_flow_run(self, flow_run_id):
        return SimpleNamespace(
            state_type=SimpleNamespace(value="COMPLETED"),
            state_name="Completed",
            end_time=None,
        )


def test_sync_running_jobs_sends_blocked_feature_notification(monkeypatch):
    job = {
        "job_id": "job-1",
        "status": "running",
        "flow_run_id": "fr-1",
        "feature_id": "FEAT-1",
        "title": "Feature 1",
        "summary": "Summary 1",
    }
    sent: list[dict] = []

    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: _CompletedClient())
    monkeypatch.setattr(
        dispatcher,
        "find_record",
        lambda *args, **kwargs: {
            "status": FeatureStatus.PIPELINE_INVALID.value,
            "blocker_reasons": ["Planner wave plan JSON markers were not found"],
        },
    )
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: {"job_id": job_id, **updates})
    monkeypatch.setattr(dispatcher, "notify_feature_event", lambda **kwargs: sent.append(kwargs) or True)

    result = dispatcher.sync_running_jobs()

    assert result[0]["status"] == "blocked"
    assert sent
    assert sent[0]["feature_id"] == "FEAT-1"
    assert sent[0]["status"] == FeatureStatus.PIPELINE_INVALID.value
    assert "Planner wave plan JSON markers were not found" in sent[0]["blockers"][0]


def test_sync_running_jobs_sends_rework_required_notification(monkeypatch):
    job = {
        "job_id": "job-2",
        "status": "running",
        "flow_run_id": "fr-2",
        "feature_id": "FEAT-2",
        "title": "Feature 2",
        "summary": "Summary 2",
    }
    sent: list[dict] = []

    monkeypatch.setattr(dispatcher, "list_jobs", lambda: [job])
    monkeypatch.setattr(dispatcher, "get_client", lambda sync_client=True: _CompletedClient())
    monkeypatch.setattr(
        dispatcher,
        "find_record",
        lambda *args, **kwargs: {
            "status": FeatureStatus.IN_PROGRESS.value,
            "blocker_reasons": ["Architect requested focused rework on the current wave"],
        },
    )
    monkeypatch.setattr(dispatcher, "update_job", lambda job_id, **updates: {"job_id": job_id, **updates})
    monkeypatch.setattr(dispatcher, "notify_feature_event", lambda **kwargs: sent.append(kwargs) or True)

    result = dispatcher.sync_running_jobs()

    assert result[0]["status"] == "rework_required"
    assert sent
    assert sent[0]["status"] == FeatureStatus.IN_PROGRESS.value
    assert sent[0]["next_action"] == "inspect-domain-blocker"
