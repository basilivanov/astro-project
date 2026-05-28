import json
import subprocess
import sys
from pathlib import Path

from tests.test_prefect_grace_packet_branch_push_gate import (
    BRANCH,
    PACKET_ID,
    PROJECT_KEY,
    _git,
    setup_packet_branch_repo,
)


def _base_cmd(repo: Path, worktree_root: Path, worktree: Path, packet: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "prefect_grace.cli",
        "packet-branch-push-gate",
        "--packet",
        str(packet),
        "--repo-root",
        str(repo),
        "--worktree-root",
        str(worktree_root),
        "--worktree-path",
        str(worktree),
        "--project-key",
        PROJECT_KEY,
        "--packet-id",
        PACKET_ID,
        "--attempt",
        "1",
        "--base-ref",
        "main",
        "--remote",
        "origin",
        "--json",
    ]


def test_cli_packet_branch_push_gate_help_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "packet-branch-push-gate", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for flag in [
        "--packet",
        "--repo-root",
        "--worktree-root",
        "--worktree-path",
        "--project-key",
        "--packet-id",
        "--attempt",
        "--base-ref",
        "--remote",
        "--dry-run",
        "--apply",
        "--commit",
        "--push",
        "--allow-git-commit",
        "--allow-git-push",
        "--json",
    ]:
        assert flag in result.stdout
    assert "--merge" not in result.stdout
    assert "--force" not in result.stdout
    assert "--target-branch" not in result.stdout
    assert "--i-understand-merge" not in result.stdout


def test_cli_packet_branch_push_gate_dry_run_json_envelope(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")
    base_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()

    result = subprocess.run(
        [
            *_base_cmd(repo, worktree_root, worktree, packet),
            "--commit",
            "--push",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert len(result.stdout) < 12000
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "packet-branch-push-gate"
    assert payload["result"] == payload["data"]
    assert payload["data"]["dry_run"] is True
    assert payload["data"]["status"] == "planned"
    assert payload["data"]["mutations"]["commit"] == "planned"
    assert payload["data"]["mutations"]["push"] == "planned"
    assert payload["data"]["mutations"]["merge"] == "not_available"
    assert _git(worktree, "rev-parse", "HEAD").stdout.strip() == base_head
    assert _git(worktree, "status", "--porcelain").stdout.strip()


def test_cli_packet_branch_push_gate_apply_without_approval_exits_1(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = subprocess.run(
        [
            *_base_cmd(repo, worktree_root, worktree, packet),
            "--apply",
            "--commit",
            "--push",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["result"] == payload["data"]
    assert payload["data"]["status"] == "blocked"
    assert {blocker["code"] for blocker in payload["errors"]} == {
        "commit_requires_approval",
        "push_requires_approval",
    }


def test_cli_packet_branch_push_gate_push_apply_temp_bare_remote(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = subprocess.run(
        [
            *_base_cmd(repo, worktree_root, worktree, packet),
            "--apply",
            "--commit",
            "--push",
            "--allow-git-commit",
            "--allow-git-push",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["mutations"]["commit"] == "applied"
    assert payload["data"]["mutations"]["push"] == "applied"
    assert payload["data"]["pushed_ref"] == f"origin/{BRANCH}"
    packet_ref = _git(bare, "show-ref", f"refs/heads/{BRANCH}").stdout.strip()
    assert payload["data"]["pushed_commit_sha"] in packet_ref
    assert _git(bare, "show-ref", "refs/heads/main", check=False).returncode != 0


def test_cli_packet_branch_push_gate_merge_flag_is_rejected(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)

    result = subprocess.run(
        [
            *_base_cmd(repo, worktree_root, worktree, packet),
            "--merge",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "unrecognized arguments: --merge" in result.stderr
