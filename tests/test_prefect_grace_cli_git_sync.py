import json
import subprocess
import sys
from pathlib import Path

from tests.test_prefect_grace_git_sync import BRANCH, PACKET_ID, PROJECT_KEY, _fixture, _git


def _base_cmd(packet: Path, repo: Path, worktree_root: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "prefect_grace.cli",
        "git-sync",
        "--packet",
        str(packet),
        "--repo-root",
        str(repo),
        "--worktree-root",
        str(worktree_root),
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


def test_cli_git_sync_help_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "git-sync", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for flag in [
        "--packet",
        "--repo-root",
        "--worktree-root",
        "--project-key",
        "--packet-id",
        "--attempt",
        "--base-ref",
        "--remote",
        "--dry-run",
        "--apply",
        "--json",
    ]:
        assert flag in result.stdout


def test_cli_git_sync_dry_run_json_envelope(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path)
    
    # Run once to create worktree via CLI
    result1 = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root), "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0, result1.stderr or result1.stdout
    payload1 = json.loads(result1.stdout)
    assert payload1["ok"] is True
    assert payload1["command"] == "git-sync"
    assert payload1["data"]["status"] == "planned"
    assert payload1["data"]["branch_name"] == BRANCH
    
    wt_path = Path(payload1["data"]["worktree_path"])
    (wt_path / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result2 = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root), "--dry-run"],
        capture_output=True,
        text=True,
    )

    assert result2.returncode == 0, result2.stderr or result2.stdout
    payload2 = json.loads(result2.stdout)
    assert payload2["ok"] is True
    assert payload2["data"]["status"] == "planned"


def test_cli_git_sync_blocked_apply_exits_1(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path, review=False)

    result = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root), "--apply"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["data"]["status"] == "blocked"
    assert any(blocker["code"] == "missing_accepted_review" for blocker in payload["errors"])


def test_cli_git_sync_commit_and_push_apply(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path)
    
    # Pre-create worktree via CLI dry-run
    res_dry = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root), "--dry-run"],
        capture_output=True,
        text=True,
    )
    payload_dry = json.loads(res_dry.stdout)
    wt_path = Path(payload_dry["data"]["worktree_path"])
    
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    _git(wt_path, "remote", "set-url", "origin", str(bare))
    
    (wt_path / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root), "--apply"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["status"] == "applied"
    assert payload["data"]["commit_sha"] is not None
    assert payload["data"]["pushed_ref"] == f"origin/{BRANCH}"
    assert _git(bare, "show-ref", f"refs/heads/{BRANCH}").returncode == 0
