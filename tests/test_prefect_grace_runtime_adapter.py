import pytest
from prefect_grace.platform.runtime_adapter import (
    WorkflowRuntime,
    DryRunRuntime,
    PrefectRuntimeAdapter,
    create_runtime,
)


def test_dry_run_runtime_submit():
    runtime = DryRunRuntime()
    packet = {"packet_id": "P1", "feature_id": "F1"}
    parameters = {"timeout": 3600}

    run_ref = runtime.submit_packet_run(packet, parameters)

    assert run_ref["runtime"] == "dry-run"
    assert run_ref["packet_id"] == "P1"
    assert "run_id" in run_ref
    assert run_ref["run_id"].startswith("dry-run-")
    assert len(runtime.submitted_runs) == 1


def test_dry_run_runtime_publish_artifact():
    runtime = DryRunRuntime()
    run_ref = {"run_id": "dry-run-123"}

    runtime.publish_artifact(run_ref, "test-artifact", "# Test Content")

    assert len(runtime.artifacts) == 1
    assert runtime.artifacts[0]["name"] == "test-artifact"
    assert runtime.artifacts[0]["body"] == "# Test Content"


def test_dry_run_runtime_read_status():
    runtime = DryRunRuntime()
    run_ref = {"run_id": "dry-run-123"}

    status = runtime.read_run_status(run_ref)

    assert status["run_id"] == "dry-run-123"
    assert status["state"] == "DRY_RUN"
    assert status["status"] == "simulated"


def test_dry_run_runtime_multiple_submissions():
    runtime = DryRunRuntime()

    ref1 = runtime.submit_packet_run({"packet_id": "P1", "feature_id": "F1"}, {})
    ref2 = runtime.submit_packet_run({"packet_id": "P2", "feature_id": "F2"}, {})

    assert len(runtime.submitted_runs) == 2
    assert ref1["run_id"] != ref2["run_id"]


def test_create_runtime_dry_run():
    runtime = create_runtime("dry-run")
    assert isinstance(runtime, DryRunRuntime)
    assert runtime.name == "dry-run"


def test_create_runtime_prefect():
    runtime = create_runtime("prefect", {"work_pool": "test-pool", "queue": "test-queue"})
    assert isinstance(runtime, PrefectRuntimeAdapter)
    assert runtime.name == "prefect"
    assert runtime.work_pool == "test-pool"
    assert runtime.queue == "test-queue"


def test_create_runtime_unknown():
    with pytest.raises(ValueError, match="Unknown runtime type"):
        create_runtime("unknown-runtime")


def test_prefect_runtime_adapter_init():
    adapter = PrefectRuntimeAdapter(work_pool="pool1", queue="queue1")
    assert adapter.name == "prefect"
    assert adapter.work_pool == "pool1"
    assert adapter.queue == "queue1"


def test_dry_run_artifact_with_dict():
    runtime = DryRunRuntime()
    run_ref = {"run_id": "dry-run-456"}
    artifact_body = {"key": "value", "count": 42}

    runtime.publish_artifact(run_ref, "json-artifact", artifact_body)

    assert len(runtime.artifacts) == 1
    assert runtime.artifacts[0]["body"] == artifact_body
