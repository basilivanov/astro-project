import json
import subprocess
import sys
from pathlib import Path

from tests.test_prefect_grace_git_mutation_gate import BRANCH, PACKET_ID, PROJECT_KEY, _fixture, _git


def _base_cmd(packet: Path, repo: Path, worktree_root: Path, worktree: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "prefect_grace.cli",
        "git-mutation-gate",
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
        "--target-branch",
        "main",
        "--remote",
        "origin",
        "--json",
    ]


def test_cli_git_mutation_gate_help_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "git-mutation-gate", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for flag in [
        "--packet",
        "--repo-root",
        "--worktree-root",
        "--worktree-path",
        "--dry-run",
        "--apply",
        "--commit",
        "--push",
        "--merge",
        "--i-understand-merge",
        "--json",
    ]:
        assert flag in result.stdout


def test_cli_git_mutation_gate_dry_run_json_envelope(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root, worktree), "--dry-run", "--commit"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "git-mutation-gate"
    assert payload["result"] == payload["data"]
    assert payload["data"]["status"] == "planned"
    assert payload["data"]["mutations"]["commit"] == "planned"
    assert payload["data"]["commit_sha"] is None


def test_cli_git_mutation_gate_blocked_apply_exits_1(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path, review=False)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root, worktree), "--apply", "--commit"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert payload["data"]["status"] == "blocked"
    assert any(blocker["code"] == "missing_accepted_review" for blocker in payload["errors"])


def test_cli_git_mutation_gate_commit_and_push_apply(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = subprocess.run(
        [*_base_cmd(packet, repo, worktree_root, worktree), "--apply", "--commit", "--push"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"] == payload["data"]
    assert payload["data"]["mutations"]["commit"] == "applied"
    assert payload["data"]["mutations"]["push"] == "applied"
    assert payload["data"]["pushed_ref"] == f"origin/{BRANCH}"
    assert _git(bare, "show-ref", f"refs/heads/{BRANCH}").returncode == 0
