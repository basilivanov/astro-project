from pathlib import Path

from prefect_grace.tasks import state_store
from prefect_grace.tasks.job_queue import claim_next_job, enqueue_feature_job, list_jobs, update_job


def test_enqueue_and_claim_job(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path
    feature_id = "FEAT-QUEUE-UNIT-1"
    job = enqueue_feature_job(
        feature_id=feature_id,
        title="Queue test",
        summary="Ensure jobs can be queued",
        execute=False,
    )
    assert job["feature_id"] == feature_id
    assert job["run_planner"] is None

    claimed = claim_next_job()
    assert claimed is not None
    assert claimed["job_id"] == job["job_id"]
    assert claimed["status"] == "dispatching"

    updated = update_job(job["job_id"], status="completed")
    assert updated["status"] == "completed"
    assert any(item["job_id"] == job["job_id"] for item in list_jobs())


def test_enqueue_job_can_request_optional_planner(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path
    job = enqueue_feature_job(
        feature_id="FEAT-QUEUE-PLANNER",
        title="Queue planner test",
        summary="Ensure optional planner flag is persisted",
        run_planner=True,
    )

    assert job["run_planner"] is True
