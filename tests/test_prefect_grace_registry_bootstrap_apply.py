import json
import subprocess
import sys
from pathlib import Path

from prefect_grace.platform.registry_bootstrap_apply import run_registry_bootstrap_apply
from prefect_grace.platform.state_store import PacketRegistryStore


def _write_project_config(path: Path, *, repo_root: Path, packets_dir: Path, runtime_root: Path) -> None:
    path.write_text(
        f"""version: 1
project_key: test-project
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


def _write_strict_packet(
    packets_dir: Path,
    feature_id: str,
    packet_id: str,
    *,
    status: str = "ready",
    depends_on: list[str] | None = None,
) -> Path:
    packet_dir = packets_dir / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    depends_line = f"- depends_on: `{', '.join(depends_on)}`\n" if depends_on else ""
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(
        f"""# Execution Packet: {packet_id}

## Objective
Test packet.

## Slice
- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `{status}`
{depends_line}
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


def _fixture_project(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    runtime_root = tmp_path / "runtime"
    repo_root.mkdir()
    config = tmp_path / "project.yaml"
    _write_project_config(config, repo_root=repo_root, packets_dir=packets_dir, runtime_root=runtime_root)
    return config, repo_root, packets_dir, runtime_root


def test_registry_bootstrap_apply_dry_run_is_default_and_read_only(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    packet = _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    (packet.parent / "SUMMARY.md").write_text("current_status: accepted\n", encoding="utf-8")

    result = run_registry_bootstrap_apply(project_config=config)

    assert result.ok is True
    assert result.dry_run is True
    assert result.apply is False
    assert result.preflight["source_packet_candidate_count"] == 1
    assert result.preflight["planned_upserts"][0]["target_status"] == "accepted"
    assert result.submit_dry_run["prefect_runs_created"] == 0
    assert not (runtime_root / "state" / "packet_registry.yaml").exists()
    assert result.source_mutations == []


def test_registry_bootstrap_apply_writes_only_runtime_root_and_is_idempotent(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    parent = _write_strict_packet(packets_dir, "FEAT-BASE", "FEAT-BASE-W01-PACKET")
    child = _write_strict_packet(
        packets_dir,
        "FEAT-CHILD",
        "FEAT-CHILD-W01-PACKET",
        depends_on=["FEAT-BASE-W01-PACKET"],
    )
    (parent.parent / "REVIEWS").mkdir()
    (parent.parent / "REVIEWS" / "review-0001.md").write_text("verdict: ACCEPTED\n", encoding="utf-8")
    before_parent = parent.read_text(encoding="utf-8")
    before_child = child.read_text(encoding="utf-8")

    result = run_registry_bootstrap_apply(project_config=config, apply=True)

    assert result.ok is True
    registry = PacketRegistryStore(runtime_root / "state")
    assert registry.load_packet("FEAT-BASE-W01-PACKET")["registry_status"] == "accepted"
    assert registry.load_packet("FEAT-CHILD-W01-PACKET")["registry_status"] == "ready"
    assert Path(result.backup_path).is_file()
    assert str(Path(result.backup_path).resolve()).startswith(str(runtime_root.resolve()))
    assert result.writes_outside_runtime_state_root == []
    assert result.source_mutations == []
    assert parent.read_text(encoding="utf-8") == before_parent
    assert child.read_text(encoding="utf-8") == before_child
    assert result.idempotence["planned_upserts_after_apply"] == []
    assert result.submit_dry_run["prefect_runs_created"] == 0


def test_registry_bootstrap_apply_packet_filter_scopes_dry_run_and_apply(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    _write_strict_packet(packets_dir, "FEAT-TWO", "FEAT-TWO-W01-PACKET")

    dry_run = run_registry_bootstrap_apply(
        project_config=config,
        packet_ids=["FEAT-TWO-W01-PACKET", "FEAT-TWO-W01-PACKET"],
    )

    assert dry_run.ok is True
    assert dry_run.packet_ids == ["FEAT-TWO-W01-PACKET"]
    assert dry_run.packet_filter == {
        "enabled": True,
        "packet_ids": ["FEAT-TWO-W01-PACKET"],
    }
    assert dry_run.preflight["source_packet_candidate_count"] == 1
    assert dry_run.source_files_checked == 1
    assert [
        item["packet_id"]
        for item in dry_run.preflight["planned_upserts"]
    ] == ["FEAT-TWO-W01-PACKET"]

    apply = run_registry_bootstrap_apply(
        project_config=config,
        apply=True,
        packet_ids=["FEAT-TWO-W01-PACKET"],
    )

    registry = PacketRegistryStore(runtime_root / "state")
    assert apply.ok is True
    assert apply.apply_summary["apply_count"] == 1
    assert registry.load_packet("FEAT-TWO-W01-PACKET") is not None
    assert registry.load_packet("FEAT-ONE-W01-PACKET") is None
    assert apply.idempotence["planned_upserts_after_apply"] == []


def test_registry_bootstrap_apply_packet_filter_fails_closed_for_missing_or_blank_ids(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")

    missing = run_registry_bootstrap_apply(
        project_config=config,
        apply=True,
        packet_ids=["FEAT-ONE-W01-PACKET", "FEAT-MISSING-W01-PACKET"],
    )
    blank = run_registry_bootstrap_apply(
        project_config=config,
        apply=True,
        packet_ids=[""],
    )

    assert missing.ok is False
    assert any(error["code"] == "PACKET_FILTER_NOT_FOUND" for error in missing.errors)
    assert PacketRegistryStore(runtime_root / "state").load_packet("FEAT-ONE-W01-PACKET") is None
    assert blank.ok is False
    assert any(error["code"] == "PACKET_FILTER_INVALID" for error in blank.errors)
    assert not (runtime_root / "state" / "packet_registry.yaml").exists()


def test_registry_bootstrap_apply_does_not_trust_source_status_or_nested_passed(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, _runtime_root = _fixture_project(tmp_path)
    _write_strict_packet(packets_dir, "FEAT-SOURCE", "FEAT-SOURCE-W01-PACKET", status="accepted")
    packet = _write_strict_packet(packets_dir, "FEAT-PASSED", "FEAT-PASSED-W01-PACKET")
    evidence_dir = packet.parent / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "evidence_manifest.json").write_text(
        json.dumps({"commands": [{"name": "pytest", "status": "passed"}]}),
        encoding="utf-8",
    )

    result = run_registry_bootstrap_apply(project_config=config)
    statuses = {
        item["packet_id"]: item["target_status"]
        for item in result.preflight["planned_upserts"]
    }

    assert result.ok is True
    assert statuses["FEAT-SOURCE-W01-PACKET"] == "ready"
    assert statuses["FEAT-PASSED-W01-PACKET"] == "ready"


def test_registry_bootstrap_apply_preserves_existing_terminal_with_unchanged_hash(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    packet = _write_strict_packet(packets_dir, "FEAT-EXISTING", "FEAT-EXISTING-W01-PACKET")
    dry_run = run_registry_bootstrap_apply(project_config=config)
    source_hash = dry_run.preflight["planned_upserts"][0]["source_hash"]
    registry = PacketRegistryStore(runtime_root / "state")
    registry.upsert_packet(
        {
            "packet_id": "FEAT-EXISTING-W01-PACKET",
            "source_hash": source_hash,
            "registry_status": "accepted",
        }
    )

    result = run_registry_bootstrap_apply(project_config=config, apply=True)

    assert result.ok is True
    assert registry.load_packet("FEAT-EXISTING-W01-PACKET")["registry_status"] == "accepted"
    assert result.apply_summary["apply_count"] == 0
    assert packet.exists()


def test_registry_bootstrap_apply_rejects_forbidden_runtime_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    forbidden_runtime = repo_root / ".worktrees" / "state"
    repo_root.mkdir()
    config = tmp_path / "project.yaml"
    _write_project_config(config, repo_root=repo_root, packets_dir=packets_dir, runtime_root=forbidden_runtime)
    _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")

    result = run_registry_bootstrap_apply(project_config=config, apply=True)

    assert result.ok is False
    assert any(error["code"] == "UNSAFE_RUNTIME_STATE_ROOT" for error in result.errors)
    assert not (forbidden_runtime / "state" / "packet_registry.yaml").exists()


def test_registry_bootstrap_apply_cli_json_envelope(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, _runtime_root = _fixture_project(tmp_path)
    _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "registry-bootstrap-apply",
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
    assert payload["command"] == "registry-bootstrap-apply"
    assert payload["result"] == payload["data"]
    assert payload["data"]["dry_run"] is True
    assert payload["data"]["submit_dry_run"]["prefect_runs_created"] == 0


def test_registry_bootstrap_apply_cli_packet_id_filter_json(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, _runtime_root = _fixture_project(tmp_path)
    _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    _write_strict_packet(packets_dir, "FEAT-TWO", "FEAT-TWO-W01-PACKET")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "registry-bootstrap-apply",
            "--project",
            str(config),
            "--packet-id",
            "FEAT-TWO-W01-PACKET",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["result"] == payload["data"]
    assert payload["data"]["packet_ids"] == ["FEAT-TWO-W01-PACKET"]
    assert payload["data"]["preflight"]["source_packet_candidate_count"] == 1
    assert payload["data"]["preflight"]["planned_upserts"][0]["packet_id"] == "FEAT-TWO-W01-PACKET"


def test_bootstrap_backlog_apply_requires_explicit_project() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "bootstrap-backlog",
            "--apply",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "requires explicit --project" in payload["errors"][0]["message"]
