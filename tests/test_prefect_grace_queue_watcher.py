import argparse
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from prefect_grace.platform.queue_watcher import QueueWatcherDaemon, QueueWatcherStats
from prefect_grace.platform.project_adapter import ProjectAdapterConfig
from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.state_store import PacketRegistryStore
from prefect_grace.platform.prefect_native_submission import NativeSubmissionResult, PacketSubmissionRecord
from prefect_grace.cli_commands.queue_watcher import _cmd_queue_watcher


class MockProjectAdapter:
    def __init__(self, repo_root, packets_dir, runtime_state_root):
        self.project_key = "test-project"
        self.repo_root = repo_root
        self.packets_dir = packets_dir
        self.runtime_state_root = runtime_state_root


def _write_strict_packet(
    packets_dir: Path,
    packet_id: str,
    *,
    depends_on: list[str] | None = None,
    status: str = "ready",
) -> Path:
    dependency_line = (
        f"- depends_on: `{', '.join(depends_on)}`\n"
        if depends_on
        else ""
    )
    packet_file = packets_dir / f"{packet_id}.md"
    packet_file.write_text(f"""# Execution Packet: {packet_id}

## Objective
Test objective

## Slice
- packet_id: `{packet_id}`
- feature_id: `FEAT-TEST`
- wave_id: `W01`
- status: `{status}`
{dependency_line}
## Allowed Write Scope
- file.py

## Frozen Scope
- other.py

## Must Preserve
- invariant

## Verification
pytest

## Expected Evidence
- test results

## Escalation Triggers
- scope violation
""", encoding="utf-8")
    return packet_file


def test_daemon_stats_serialization():
    stats = QueueWatcherStats(
        iterations=5,
        packets_synced=10,
        draft_monitored=3,
        ready_monitored=7,
        submitted_count=4,
        errors=["err1"],
    )
    data = stats.to_dict()
    assert data["iterations"] == 5
    assert data["packets_synced"] == 10
    assert data["draft_monitored"] == 3
    assert data["ready_monitored"] == 7
    assert data["submitted_count"] == 4
    assert data["errors"] == ["err1"]


def test_daemon_empty_directory(tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    daemon = QueueWatcherDaemon(
        project=project,
        interval_seconds=1.0,
        once=True,
        launch_drafts=False,
    )

    stats = daemon.start()
    assert stats["iterations"] == 1
    assert stats["packets_synced"] == 0
    assert stats["draft_monitored"] == 0
    assert stats["ready_monitored"] == 0
    assert stats["submitted_count"] == 0
    assert not stats["errors"]


@patch("prefect_grace.platform.queue_watcher.submit_ready_packets_to_prefect")
def test_daemon_submits_ready_packet(mock_submit, tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    _write_strict_packet(packets_dir, "FEAT-TEST-P1", status="ready")

    project = MockProjectAdapter(tmp_path, "packets", state_root)

    rec = PacketSubmissionRecord(
        packet_id="FEAT-TEST-P1",
        feature_id="FEAT-TEST",
        wave_id="W01",
        attempt=1,
        source_hash="hash",
        idempotency_key="key",
        flow_run_id="run-id",
        flow_run_name="run-name",
        deployment_name="dep",
        work_queue_name="wq",
        status="submitted",
    )
    mock_result = NativeSubmissionResult(
        ok=True,
        project_key="test-project",
        dry_run=False,
        packets_planned=["FEAT-TEST-P1"],
        packets_submitted=["FEAT-TEST-P1"],
        records=[rec],
        blocked_packets=[],
        warnings=[],
        errors=[],
    )
    mock_submit.return_value = mock_result

    daemon = QueueWatcherDaemon(
        project=project,
        interval_seconds=1.0,
        once=True,
        launch_drafts=False,
    )

    stats = daemon.start()
    assert stats["iterations"] == 1
    assert stats["packets_synced"] == 1
    assert stats["draft_monitored"] == 0
    assert stats["ready_monitored"] == 1
    assert stats["submitted_count"] == 1
    assert not stats["errors"]

    mock_submit.assert_called_once()


@patch("prefect_grace.platform.queue_watcher.submit_ready_packets_to_prefect")
def test_daemon_ignores_draft_packet_by_default(mock_submit, tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    _write_strict_packet(packets_dir, "FEAT-TEST-P1", status="draft")

    project = MockProjectAdapter(tmp_path, "packets", state_root)

    daemon = QueueWatcherDaemon(
        project=project,
        interval_seconds=1.0,
        once=True,
        launch_drafts=False,
    )

    stats = daemon.start()
    assert stats["iterations"] == 1
    assert stats["packets_synced"] == 1
    assert stats["draft_monitored"] == 1
    assert stats["ready_monitored"] == 0
    assert stats["submitted_count"] == 0
    assert not stats["errors"]

    mock_submit.assert_not_called()


@patch("prefect_grace.platform.queue_watcher.submit_ready_packets_to_prefect")
def test_daemon_submits_draft_when_requested(mock_submit, tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    _write_strict_packet(packets_dir, "FEAT-TEST-P1", status="draft")

    project = MockProjectAdapter(tmp_path, "packets", state_root)

    rec = PacketSubmissionRecord(
        packet_id="FEAT-TEST-P1",
        feature_id="FEAT-TEST",
        wave_id="W01",
        attempt=1,
        source_hash="hash",
        idempotency_key="key",
        flow_run_id="run-id",
        flow_run_name="run-name",
        deployment_name="dep",
        work_queue_name="wq",
        status="submitted",
    )
    mock_result = NativeSubmissionResult(
        ok=True,
        project_key="test-project",
        dry_run=False,
        packets_planned=["FEAT-TEST-P1"],
        packets_submitted=["FEAT-TEST-P1"],
        records=[rec],
        blocked_packets=[],
        warnings=[],
        errors=[],
    )
    mock_submit.return_value = mock_result

    daemon = QueueWatcherDaemon(
        project=project,
        interval_seconds=1.0,
        once=True,
        launch_drafts=True,
    )

    stats = daemon.start()
    assert stats["iterations"] == 1
    assert stats["packets_synced"] == 1
    assert stats["draft_monitored"] == 1
    assert stats["ready_monitored"] == 0
    assert stats["submitted_count"] == 1
    assert not stats["errors"]

    mock_submit.assert_called_once()


@patch("prefect_grace.cli_commands.queue_watcher._load_adapter_from_args")
@patch("prefect_grace.cli_commands.queue_watcher.QueueWatcherDaemon")
def test_cli_command_invocation(mock_daemon_class, mock_load_adapter):
    mock_project = MagicMock()
    mock_project.project_key = "cli-test"
    mock_load_adapter.return_value = mock_project

    mock_daemon_inst = MagicMock()
    mock_daemon_inst.start.return_value = {
        "iterations": 1,
        "packets_synced": 5,
        "draft_monitored": 2,
        "ready_monitored": 3,
        "submitted_count": 2,
        "errors": [],
    }
    mock_daemon_class.return_value = mock_daemon_inst

    args = argparse.Namespace(
        project="path/to/project.yaml",
        interval=10.0,
        once=True,
        launch_drafts=True,
        runner="managed",
        json=False,
    )

    _cmd_queue_watcher(args)

    mock_load_adapter.assert_called_once_with(args)
    mock_daemon_class.assert_called_once_with(
        project=mock_project,
        interval_seconds=10.0,
        once=True,
        launch_drafts=True,
        runner_kind="managed",
    )
    mock_daemon_inst.start.assert_called_once()
