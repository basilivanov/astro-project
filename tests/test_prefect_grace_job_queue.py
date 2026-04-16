from pathlib import Path

from prefect_grace.tasks import state_store
from prefect_grace.tasks.job_queue import (
    JOB_STATUS_ACCEPTED,
    JOB_STATUS_AWAITING_COMMIT,
    JOB_STATUS_PENDING,
    JOB_STATUS_SCHEDULED,
    claim_next_job,
    enqueue_canonical_feature_sequence,
    enqueue_feature_job,
    list_jobs,
    list_sequences,
    update_job,
)


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


def test_enqueue_sequence_marks_only_first_job_scheduled(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path
    (tmp_path / "features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "  - feature_id: FEAT-SEQ-1",
                "    title: Feature one",
                "    summary: Summary one",
                "  - feature_id: FEAT-SEQ-2",
                "    title: Feature two",
                "    summary: Summary two",
            ]
        ),
        encoding="utf-8",
    )

    sequence = enqueue_canonical_feature_sequence(feature_ids=["FEAT-SEQ-1", "FEAT-SEQ-2"])
    jobs = list_jobs()
    sequences = list_sequences()

    assert sequence["status"] == JOB_STATUS_SCHEDULED
    assert [job["feature_id"] for job in jobs] == ["FEAT-SEQ-1", "FEAT-SEQ-2"]
    assert jobs[0]["status"] == JOB_STATUS_SCHEDULED
    assert jobs[1]["status"] == JOB_STATUS_PENDING
    assert jobs[0]["sequence_label_ru"] == "Фича 1/2"
    assert jobs[1]["status_summary_ru"] == "Фича 2/2: запланирована и ждёт своей очереди."
    assert sequences[0]["feature_ids"] == ["FEAT-SEQ-1", "FEAT-SEQ-2"]
    assert sequences[0]["current_label_ru"] == "Фича 1/2"


def test_sequence_advances_only_after_terminal_status(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path
    (tmp_path / "features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "  - feature_id: FEAT-SEQ-ADV-1",
                "    title: Feature one",
                "    summary: Summary one",
                "  - feature_id: FEAT-SEQ-ADV-2",
                "    title: Feature two",
                "    summary: Summary two",
            ]
        ),
        encoding="utf-8",
    )

    enqueue_canonical_feature_sequence(feature_ids=["FEAT-SEQ-ADV-1", "FEAT-SEQ-ADV-2"])

    first = claim_next_job()
    assert first is not None
    assert first["feature_id"] == "FEAT-SEQ-ADV-1"

    assert claim_next_job() is None

    finished = update_job(first["job_id"], status=JOB_STATUS_AWAITING_COMMIT)
    jobs = list_jobs()
    sequences = list_sequences()

    assert finished["status"] == JOB_STATUS_AWAITING_COMMIT
    assert finished["status_summary_ru"] == "Фича 1/2: ждёт коммита. Перехожу к следующей."
    assert jobs[1]["status"] == JOB_STATUS_SCHEDULED
    assert sequences[0]["current_label_ru"] == "Фича 2/2"
    assert sequences[0]["summary_ru"] == "Фича 2/2: запланирована."

    second = claim_next_job()
    assert second is not None
    assert second["feature_id"] == "FEAT-SEQ-ADV-2"
    assert second["status"] == "dispatching"


def test_sequence_has_priority_over_unrelated_single_jobs_after_advance(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path
    (tmp_path / "features.yaml").write_text(
        "\n".join(
            [
                "features:",
                "  - feature_id: FEAT-SEQ-PRI-1",
                "    title: Feature one",
                "    summary: Summary one",
                "  - feature_id: FEAT-SEQ-PRI-2",
                "    title: Feature two",
                "    summary: Summary two",
            ]
        ),
        encoding="utf-8",
    )

    enqueue_canonical_feature_sequence(feature_ids=["FEAT-SEQ-PRI-1", "FEAT-SEQ-PRI-2"])
    single = enqueue_feature_job(feature_id="FEAT-SINGLE-PRI", title="Single", summary="Single summary")

    first = claim_next_job()
    assert first is not None
    assert first["feature_id"] == "FEAT-SEQ-PRI-1"

    update_job(first["job_id"], status=JOB_STATUS_ACCEPTED)
    second = claim_next_job()

    assert second is not None
    assert second["feature_id"] == "FEAT-SEQ-PRI-2"
    assert second["job_id"] != single["job_id"]


def test_single_feature_lock_blocks_parallel_claim_for_same_feature(tmp_path: Path) -> None:
    state_store.STATE_DIR = tmp_path
    first = enqueue_feature_job(feature_id="FEAT-LOCK-1", title="Lock one", summary="First")
    second = enqueue_feature_job(feature_id="FEAT-LOCK-1", title="Lock one again", summary="Second")

    claimed = claim_next_job()
    assert claimed is not None
    assert claimed["job_id"] == first["job_id"]

    blocked = claim_next_job()
    assert blocked is None

    update_job(first["job_id"], status=JOB_STATUS_ACCEPTED)
    next_claim = claim_next_job()
    assert next_claim is not None
    assert next_claim["job_id"] == second["job_id"]
