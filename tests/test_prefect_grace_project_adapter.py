from pathlib import Path

import pytest
from prefect_grace.platform.project_adapter import load_project_adapter


def test_load_project_adapter_defaults(tmp_path: Path) -> None:
    # Use existing project.yaml for default test, or mock one
    config_file = tmp_path / "project.yaml"
    config_file.write_text(
        """version: 1
project_key: test-project
repo_root: /opt/test-project
default_branch: main
grace_dir: grace
packets_dir: packets
runtime_state_root: /var/lib/grace/test-project
artifact_root: /var/lib/grace/test-project/artifacts
worktree_root: /var/lib/grace/test-project/worktrees
workflow_runtime: prefect
prefect:
  work_pool: test-pool
  live_queue: test-live
  monitoring_queue: test-mon
agent_executor:
  default: cli
  command: execute
""",
        encoding="utf-8",
    )

    adapter = load_project_adapter(config_path=config_file)
    assert adapter.version == 1
    assert adapter.project_key == "test-project"
    assert adapter.repo_root == "/opt/test-project"
    assert adapter.prefect.work_pool == "test-pool"
    assert adapter.agent_executor.default == "cli"


def test_load_project_adapter_overrides(tmp_path: Path) -> None:
    config_file = tmp_path / "project.yaml"
    config_file.write_text(
        """version: 1
project_key: test-project
repo_root: /opt/test-project
default_branch: main
prefect:
  work_pool: test-pool
""",
        encoding="utf-8",
    )

    overrides = {
        "project_key": "override-key",
        "prefect": {"work_pool": "override-pool"},
    }

    adapter = load_project_adapter(config_path=config_file, overrides=overrides)
    assert adapter.project_key == "override-key"
    assert adapter.prefect.work_pool == "override-pool"


def test_load_project_adapter_missing() -> None:
    with pytest.raises(FileNotFoundError):
        load_project_adapter(config_path=Path("/nonexistent/project.yaml"))
