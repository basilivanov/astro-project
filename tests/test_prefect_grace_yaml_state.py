from pathlib import Path

from prefect_grace.platform.state_store import (
    ExecutorHistoryStore,
    PacketRegistryStore,
    RunStore,
)


def test_packet_registry_store(tmp_path: Path) -> None:
    store = PacketRegistryStore(tmp_path)
    packet = {
        "packet_id": "FEAT-TEST-W01",
        "title": "Test Packet",
        "status": "draft",
    }

    # Upsert
    store.upsert_packet(packet)

    # Load
    loaded = store.load_packet("FEAT-TEST-W01")
    assert loaded == packet

    # List
    packets = store.list_packets()
    assert len(packets) == 1
    assert packets[0] == packet


def test_run_store(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    record = {
        "feature_id": "FEAT-TEST",
        "status": "running",
    }

    # Create
    run_id = store.create_run(record)
    assert run_id != ""

    # Get
    run = store.get_run(run_id)
    assert run["run_id"] == run_id
    assert run["feature_id"] == "FEAT-TEST"
    assert run["status"] == "running"

    # Update
    store.update_run(run_id, {"status": "completed", "ended_at": "now"})
    updated = store.get_run(run_id)
    assert updated["status"] == "completed"
    assert updated["ended_at"] == "now"


def test_executor_history_store(tmp_path: Path) -> None:
    store = ExecutorHistoryStore(tmp_path)
    execution = {
        "packet_id": "FEAT-TEST-W01",
        "executor": "codex1",
        "duration": 42.0,
    }

    # Append
    store.append_execution(execution)

    # List
    executions = store.list_executions()
    assert len(executions) == 1
    assert executions[0] == execution
