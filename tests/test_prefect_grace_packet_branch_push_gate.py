import json
import subprocess
from pathlib import Path

from prefect_grace.platform.packet_branch_push_gate import run_packet_branch_push_gate


PACKET_ID = "FEAT-PACKET-BRANCH-PUSH-W01-PACKET"
PROJECT_KEY = "astro-project"
BRANCH = f"agent/{PROJECT_KEY}/{PACKET_ID}/attempt-0001"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def _write_packet(packet: Path) -> None:
    packet.write_text(
        f"""# Execution Packet: {PACKET_ID}

## Objective
Temp packet branch push gate packet.

## Slice
- packet_id: `{PACKET_ID}`
- feature_id: `FEAT-PACKET-BRANCH-PUSH`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- allowed/**

## Frozen Scope
- frozen/**

## Must Preserve
- Packet branch push stays guarded.

## Verification
pytest

## Expected Evidence
- evidence manifest

## Escalation Triggers
- unsafe packet branch push
""",
        encoding="utf-8",
    )


def _write_review(packet_dir: Path, accepted: bool = True) -> None:
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir(parents=True, exist_ok=True)
    status = "accepted" if accepted else "rework_required"
    (reviews / "review-0001.md").write_text(f"status: {status}\n\n## Verdict\n{status}\n", encoding="utf-8")


def _write_evidence(packet_dir: Path, valid: bool = True) -> None:
    evidence_dir = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    if valid:
        (evidence_dir / "targeted_pytest.txt").write_text("1 passed\n", encoding="utf-8")
    artifact = "targeted_pytest.txt" if valid else "missing.txt"
    (evidence_dir / "evidence_manifest.json").write_text(
        json.dumps(
            {
                "packet_id": PACKET_ID,
                "generated_by": "pytest",
                "evidence": [
                    {
                        "id": "EV-PACKET-BRANCH-PUSH-001",
                        "status": "collected",
                        "stage": "packet_local",
                        "producer": "pytest",
                        "artifact_paths": [artifact],
                        "summary": "packet branch push gate proof",
                    }
                ],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )


def setup_packet_branch_repo(
    tmp_path: Path,
    *,
    review: bool = True,
    evidence: bool = True,
) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    worktree_root = tmp_path / "worktrees"
    worktree = worktree_root / "packet-attempt-0001"
    repo.mkdir()
    worktree_root.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    packet_dir = repo / "packets" / "FEAT-PACKET-BRANCH-PUSH"
    packet_dir.mkdir(parents=True)
    packet = packet_dir / "EXECUTION_PACKET.md"
    _write_packet(packet)
    if review:
        _write_review(packet_dir)
    if evidence:
        _write_evidence(packet_dir)
    (repo / "allowed").mkdir()
    (repo / "allowed" / ".gitkeep").write_text("", encoding="utf-8")
    (repo / "frozen").mkdir()
    (repo / "frozen" / ".gitkeep").write_text("", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    _git(repo, "worktree", "add", "-b", BRANCH, str(worktree), "main")
    _git(worktree, "config", "user.email", "test@example.invalid")
    _git(worktree, "config", "user.name", "Test User")
    return repo, worktree_root, worktree, packet


def run_gate(packet: Path, repo: Path, worktree_root: Path, worktree: Path, **kwargs):
    return run_packet_branch_push_gate(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        worktree_path=worktree,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        remote="origin",
        **kwargs,
    )


def test_packet_branch_push_gate_dry_run_plans_commit_and_push_without_mutation(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    base_head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(packet, repo, worktree_root, worktree, dry_run=True, commit=True, push=True)

    assert result.ok is True
    assert result.status == "planned"
    assert result.mutations["commit"] == "planned"
    assert result.mutations["push"] == "planned"
    assert result.mutations["merge"] == "not_available"
    assert result.commit_sha is None
    assert result.pushed_ref is None
    assert _git(worktree, "rev-parse", "HEAD").stdout.strip() == base_head
    assert _git(worktree, "status", "--porcelain").stdout.strip()
    assert _git(bare, "show-ref", f"refs/heads/{BRANCH}", check=False).returncode != 0


def test_packet_branch_push_gate_missing_review_blocks(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path, review=False)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        commit=True,
        approve_commit=True,
    )

    assert result.ok is False
    assert any(blocker["code"] == "missing_accepted_review" for blocker in result.blockers)


def test_packet_branch_push_gate_invalid_evidence_blocks(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path, evidence=False)
    _write_evidence(packet.parent, valid=False)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        commit=True,
        approve_commit=True,
    )

    assert result.ok is False
    assert any(blocker["code"] == "invalid_evidence_manifest" for blocker in result.blockers)


def test_packet_branch_push_gate_scope_violation_blocks(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    (worktree / "frozen" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        commit=True,
        approve_commit=True,
    )

    assert result.ok is False
    assert any(blocker["code"] == "scope_guard_failed" for blocker in result.blockers)


def test_packet_branch_push_gate_wrong_branch_blocks(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    _git(worktree, "switch", "-c", "agent/astro-project/OTHER/attempt-0001")
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        commit=True,
        approve_commit=True,
    )

    assert result.ok is False
    assert any(blocker["code"] == "packet_branch_mismatch" for blocker in result.blockers)


def test_packet_branch_push_gate_commit_only_apply_in_packet_worktree(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    base_main = _git(repo, "rev-parse", "main").stdout.strip()
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        commit=True,
        approve_commit=True,
    )

    assert result.ok is True
    assert result.status == "applied"
    assert result.mutations["commit"] == "applied"
    assert result.mutations["push"] == "not_requested"
    assert result.mutations["merge"] == "not_available"
    assert result.commit_sha
    assert _git(worktree, "rev-parse", "HEAD").stdout.strip() == result.commit_sha
    assert _git(repo, "rev-parse", "main").stdout.strip() == base_main


def test_packet_branch_push_gate_push_apply_to_temp_bare_remote_only_packet_branch(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        commit=True,
        push=True,
        approve_commit=True,
        approve_push=True,
    )

    assert result.ok is True
    assert result.mutations["commit"] == "applied"
    assert result.mutations["push"] == "applied"
    assert result.pushed_ref == f"origin/{BRANCH}"
    packet_ref = _git(bare, "show-ref", f"refs/heads/{BRANCH}").stdout.strip()
    assert result.pushed_commit_sha in packet_ref
    assert _git(bare, "show-ref", "refs/heads/main", check=False).returncode != 0


def test_packet_branch_push_gate_push_only_blocks_clean_branch_with_committed_out_of_scope_diff(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    (worktree / "frozen" / "already_committed.txt").write_text("out of scope\n", encoding="utf-8")
    _git(worktree, "add", "frozen/already_committed.txt")
    _git(worktree, "commit", "-m", "out of scope packet diff")
    assert _git(worktree, "status", "--porcelain").stdout.strip() == ""

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        push=True,
        approve_push=True,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.mutations["push"] == "blocked"
    assert result.committed_diff_total == 1
    assert result.committed_diff_sample == ["frozen/already_committed.txt"]
    assert any(blocker["code"] == "committed_diff_scope_failed" for blocker in result.blockers)
    assert _git(bare, "show-ref", f"refs/heads/{BRANCH}", check=False).returncode != 0


def test_packet_branch_push_gate_push_only_allows_clean_branch_with_committed_in_scope_diff(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    (worktree / "allowed" / "already_committed.txt").write_text("in scope\n", encoding="utf-8")
    _git(worktree, "add", "allowed/already_committed.txt")
    _git(worktree, "commit", "-m", "in scope packet diff")
    committed_sha = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    assert _git(worktree, "status", "--porcelain").stdout.strip() == ""

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        push=True,
        approve_push=True,
    )

    assert result.ok is True
    assert result.status == "applied"
    assert result.mutations["commit"] == "not_requested"
    assert result.mutations["push"] == "applied"
    assert result.committed_diff_total == 1
    assert result.committed_diff_sample == ["allowed/already_committed.txt"]
    assert result.pushed_ref == f"origin/{BRANCH}"
    packet_ref = _git(bare, "show-ref", f"refs/heads/{BRANCH}").stdout.strip()
    assert committed_sha in packet_ref
    assert result.pushed_commit_sha == committed_sha
    assert _git(bare, "show-ref", "refs/heads/main", check=False).returncode != 0


def test_packet_branch_push_gate_push_only_blocks_empty_committed_diff(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    assert _git(worktree, "status", "--porcelain").stdout.strip() == ""

    result = run_gate(
        packet,
        repo,
        worktree_root,
        worktree,
        apply=True,
        push=True,
        approve_push=True,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.mutations["push"] == "blocked"
    assert any(blocker["code"] == "empty_committed_diff_rejected" for blocker in result.blockers)
    assert _git(bare, "show-ref", f"refs/heads/{BRANCH}", check=False).returncode != 0


def test_packet_branch_push_gate_apply_requires_commit_and_push_approvals(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = setup_packet_branch_repo(tmp_path)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = run_gate(packet, repo, worktree_root, worktree, apply=True, commit=True, push=True)

    assert result.ok is False
    assert {blocker["code"] for blocker in result.blockers} == {
        "commit_requires_approval",
        "push_requires_approval",
    }


def test_packet_branch_push_gate_merge_is_unreachable() -> None:
    result = run_packet_branch_push_gate

    assert "merge" not in result.__annotations__
