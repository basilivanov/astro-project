import json
import subprocess
import sys
from pathlib import Path

from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.state_store import PacketRegistryStore


def _write_project_config(path: Path, *, repo_root: Path, packets_dir: Path, runtime_root: Path) -> None:
    path.write_text(
        f"""version: 1
project_key: cli-nightly-test
repo_root: {repo_root}
default_branch: main
grace_dir: grace
packets_dir: {packets_dir.relative_to(repo_root)}
runtime_state_root: {runtime_root}
artifact_root: {runtime_root / "artifacts"}
worktree_root: {runtime_root / "worktrees"}
workflow_runtime: prefect
prefect:
  work_pool: test-process
  live_queue: test-live
  monitoring_queue: test-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""",
        encoding="utf-8",
    )


def _write_strict_packet(packets_dir: Path, feature_id: str, packet_id: str) -> Path:
    packet_dir = packets_dir / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(
        f"""# Execution Packet: {packet_id}

## Objective
CLI nightly packet.

## Slice
- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- prefect_grace/platform/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Source packet files are immutable.

## Verification
pytest

## Expected Evidence
- test output

## Escalation Triggers
- missing evidence
""",
        encoding="utf-8",
    )
    return packet_path


def _project(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    runtime_root = tmp_path / "runtime"
    repo_root.mkdir()
    config = tmp_path / "project.yaml"
    _write_project_config(config, repo_root=repo_root, packets_dir=packets_dir, runtime_root=runtime_root)
    return config, packets_dir, runtime_root


def test_cli_run_nightly_defaults_to_dry_run_json_envelope(tmp_path: Path) -> None:
    config, packets_dir, runtime_root = _project(tmp_path)
    packet = _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    parsed = parse_packet_markdown(packet)
    PacketRegistryStore(runtime_root / "state").upsert_packet(
        {
            "packet_id": parsed.packet_id,
            "feature_id": parsed.feature_id,
            "wave_id": parsed.wave_id,
            "source_hash": parsed.source_hash,
            "path": str(packet),
            "registry_status": "accepted",
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-nightly",
            "--project",
            str(config),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "run-nightly"
    assert payload["result"] == payload["data"]
    assert payload["data"]["mode"] == "nightly_dry_run"
    assert payload["data"]["side_effects"]["prefect_runs_created"] == 0
    assert payload["data"]["lock"]["released"] is True


def test_cli_run_nightly_dry_run_until_blocked_reports_stale_registry(tmp_path: Path) -> None:
    config, packets_dir, _runtime_root = _project(tmp_path)
    packet = _write_strict_packet(packets_dir, "FEAT-ACCEPTED", "FEAT-ACCEPTED-W01-PACKET")
    (packet.parent / "SUMMARY.md").write_text("current_status: accepted\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-nightly",
            "--project",
            str(config),
            "--dry-run",
            "--until-blocked",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"] == payload["data"]
    assert payload["data"]["preflight_status"] == "blocked"
    assert payload["data"]["plan"]["stop_reason"] == "source_runtime_mismatch"
    assert payload["data"]["side_effects"]["prefect_runs_created"] == 0


def test_cli_run_nightly_execute_fails_closed(tmp_path: Path) -> None:
    config, _packets_dir, _runtime_root = _project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-nightly",
            "--project",
            str(config),
            "--execute",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "run-nightly"
    assert payload["result"] == payload["data"]
    assert payload["errors"][0]["code"] == "NIGHTLY_EXECUTION_NOT_ENABLED"
    assert payload["data"]["side_effects"]["prefect_runs_created"] == 0
    assert payload["data"]["side_effects"]["live_agents_started"] == 0
