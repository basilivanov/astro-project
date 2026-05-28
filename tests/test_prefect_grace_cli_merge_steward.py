import json
import subprocess
import sys
from pathlib import Path

from tests.test_prefect_grace_merge_steward import (
    BRANCH_1,
    BRANCH_2,
    PACKET_ID_1,
    PACKET_ID_2,
    PROJECT_KEY,
    _setup_repo,
)


def _base_cmd(repo: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "prefect_grace.cli",
        "merge-steward",
        "--repo-root",
        str(repo),
        "--target-branch",
        "main",
        "--remote",
        "origin",
        "--json",
    ]


def test_cli_merge_steward_help_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "merge-steward", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for flag in [
        "--repo-root",
        "--target-branch",
        "--packet-branch",
        "--packet-path",
        "--remote",
        "--dry-run",
        "--apply",
        "--merge",
        "--i-understand-merge",
        "--json",
    ]:
        assert flag in result.stdout


def test_cli_merge_steward_dry_run_json_envelope(tmp_path: Path) -> None:
    repo, packet_paths = _setup_repo(tmp_path)

    result = subprocess.run(
        [
            *_base_cmd(repo),
            "--dry-run",
            "--packet-branch",
            BRANCH_1,
            "--packet-path",
            f"{BRANCH_1}:{packet_paths[BRANCH_1]}",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "merge-steward"
    assert payload["result"] == payload["data"]
    assert payload["data"]["status"] == "planned"
    assert payload["data"]["plan"]["candidates_total"] == 1
    assert payload["data"]["merged_count"] == 0


def test_cli_merge_steward_blocked_apply_exits_1(tmp_path: Path) -> None:
    repo, packet_paths = _setup_repo(tmp_path)

    result = subprocess.run(
        [
            *_base_cmd(repo),
            "--apply",
            "--merge",
            "--packet-branch",
            BRANCH_1,
            "--packet-path",
            f"{BRANCH_1}:{packet_paths[BRANCH_1]}",
            # Missing --i-understand-merge
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert payload["data"]["status"] == "blocked"
    assert any(blocker["code"] == "merge_requires_cli_approval" for blocker in payload["errors"])


def test_cli_merge_steward_multiple_branches(tmp_path: Path) -> None:
    repo, packet_paths = _setup_repo(tmp_path)

    result = subprocess.run(
        [
            *_base_cmd(repo),
            "--dry-run",
            "--packet-branch",
            BRANCH_1,
            "--packet-branch",
            BRANCH_2,
            "--packet-path",
            f"{BRANCH_1}:{packet_paths[BRANCH_1]}",
            "--packet-path",
            f"{BRANCH_2}:{packet_paths[BRANCH_2]}",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["plan"]["candidates_total"] == 2
    assert payload["data"]["plan"]["excluded_total"] == 0


def test_cli_merge_steward_no_branches_warning(tmp_path: Path) -> None:
    repo, packet_paths = _setup_repo(tmp_path)

    result = subprocess.run(
        [*_base_cmd(repo), "--dry-run"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["status"] == "planned"
    assert len(payload["warnings"]) == 1
    assert payload["warnings"][0]["code"] == "no_candidates"
