import json
import subprocess
from pathlib import Path

from prefect_grace.platform.git_mutation_gate import run_git_mutation_gate


PACKET_ID = "FEAT-TEMP-W01-PACKET"
PROJECT_KEY = "astro-project"
BRANCH = f"agent/{PROJECT_KEY}/{PACKET_ID}/attempt-0001"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def _write_packet(packet: Path) -> None:
    packet.write_text(
        f"""# Execution Packet: {PACKET_ID}

## Objective
Temp git mutation packet.

## Slice
- packet_id: `{PACKET_ID}`
- feature_id: `FEAT-TEMP`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- allowed/**

## Frozen Scope
- frozen/**

## Must Preserve
- Git mutations stay guarded.

## Verification
pytest

## Expected Evidence
- evidence manifest

## Escalation Triggers
- unsafe git mutation
""",
        encoding="utf-8",
    )


def _write_review(packet_dir: Path, accepted: bool = True) -> None:
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir(parents=True, exist_ok=True)
    status = "accepted" if accepted else "rework_required"
    (reviews / "review-0001.md").write_text(f"status: {status}\n\n## Verdict\n{status}\n", encoding="utf-8")


def _write_review_yaml(packet_dir: Path, *, status: str, packet_id: str = PACKET_ID) -> None:
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / "review-0001.yaml").write_text(
        f"""schema_version: 1
artifact_type: review
packet_id: {packet_id}
status: {status}
generated_by: pytest
reviewed_at: 2026-05-28 12:34:56
summary: git mutation gate review sidecar
""",
        encoding="utf-8",
    )


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
                        "id": "EV-GIT-001",
                        "status": "collected",
                        "stage": "packet_local",
                        "producer": "pytest",
                        "artifact_paths": [artifact],
                        "summary": "git mutation gate proof",
                    }
                ],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )


def _fixture(tmp_path: Path, *, review: bool = True, evidence: bool = True) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    worktree_root = tmp_path / "worktrees"
    worktree = worktree_root / "packet-attempt-0001"
    repo.mkdir()
    worktree_root.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    packet_dir = repo / "packets" / "FEAT-TEMP"
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


def _run(packet: Path, repo: Path, worktree_root: Path, worktree: Path, **kwargs):
    return run_git_mutation_gate(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        worktree_path=worktree,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        target_branch="main",
        remote="origin",
        **kwargs,
    )


def test_git_mutation_gate_dry_run_does_not_mutate(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    base_head = _git(repo, "rev-parse", "main").stdout.strip()
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=True, commit=True)

    assert result.ok is True
    assert result.status == "planned"
    assert result.mutations["commit"] == "planned"
    assert result.commit_sha is None
    assert _git(repo, "rev-parse", "main").stdout.strip() == base_head
    assert _git(worktree, "status", "--porcelain").stdout.strip()


def test_git_mutation_gate_commit_apply_commits_only_in_packet_worktree(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    base_head = _git(repo, "rev-parse", "main").stdout.strip()
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True)

    assert result.ok is True
    assert result.status == "applied"
    assert result.mutations["commit"] == "applied"
    assert result.commit_sha
    assert _git(worktree, "rev-parse", "HEAD").stdout.strip() == result.commit_sha
    assert _git(repo, "rev-parse", "main").stdout.strip() == base_head


def test_git_mutation_gate_push_apply_pushes_only_packet_branch(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", str(bare))
    _git(repo, "remote", "add", "origin", str(bare))
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True, push=True)

    assert result.ok is True
    assert result.mutations["push"] == "applied"
    assert result.pushed_ref == f"origin/{BRANCH}"
    packet_ref = _git(bare, "show-ref", f"refs/heads/{BRANCH}").stdout.strip()
    assert result.pushed_commit_sha in packet_ref
    assert _git(bare, "show-ref", "refs/heads/main", check=False).returncode != 0


def test_git_mutation_gate_merge_without_approval_is_blocked(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, merge=True)

    assert result.ok is False
    assert result.status == "blocked"
    assert result.mutations["merge"] == "blocked"
    assert any(blocker["code"] == "merge_requires_cli_approval" for blocker in result.blockers)
    assert any(blocker["code"] == "merge_requires_env_approval" for blocker in result.blockers)


def test_git_mutation_gate_merge_apply_fast_forwards_with_approval(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")
    committed = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True)
    assert committed.ok is True

    result = _run(
        packet,
        repo,
        worktree_root,
        worktree,
        dry_run=False,
        apply=True,
        merge=True,
        understand_merge=True,
        merge_approved_env="1",
    )

    assert result.ok is True
    assert result.mutations["merge"] == "applied"
    assert result.merge_sha == committed.commit_sha
    assert _git(repo, "rev-parse", "main").stdout.strip() == committed.commit_sha


def test_git_mutation_gate_dirty_target_blocks_merge(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    (repo / "target-dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = _run(
        packet,
        repo,
        worktree_root,
        worktree,
        dry_run=False,
        apply=True,
        merge=True,
        understand_merge=True,
        merge_approved_env="1",
    )

    assert result.ok is False
    assert any(blocker["code"] == "dirty_target_branch" for blocker in result.blockers)


def test_git_mutation_gate_branch_mismatch_blocks_commit(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    _git(worktree, "switch", "-c", "agent/astro-project/OTHER/attempt-0001")
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True)

    assert result.ok is False
    assert any(blocker["code"] == "packet_branch_mismatch" for blocker in result.blockers)


def test_git_mutation_gate_missing_accepted_review_blocks_mutation(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path, review=False)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True)

    assert result.ok is False
    assert any(blocker["code"] == "missing_accepted_review" for blocker in result.blockers)


def test_git_mutation_gate_yaml_rework_overrides_markdown_accepted(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    _write_review_yaml(packet.parent, status="rework_required")
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=True, commit=True)

    assert result.ok is False
    assert result.review["present"] is True
    assert result.review["accepted"] is False
    assert result.review["source"] == "yaml"
    assert result.review["path"].endswith("review-0001.yaml")
    assert any(blocker["code"] == "missing_accepted_review" for blocker in result.blockers)


def test_git_mutation_gate_yaml_accepted_overrides_markdown_rework(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    _write_review(packet.parent, accepted=False)
    _write_review_yaml(packet.parent, status="accepted")
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=True, commit=True)

    assert result.ok is True
    assert result.review["present"] is True
    assert result.review["accepted"] is True
    assert result.review["source"] == "yaml"
    assert result.review["path"].endswith("review-0001.yaml")


def test_git_mutation_gate_yaml_packet_id_mismatch_blocks_review(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    _write_review_yaml(packet.parent, status="accepted", packet_id="FEAT-OTHER-W01-PACKET")
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=True, commit=True)

    assert result.ok is False
    assert result.review["present"] is True
    assert result.review["accepted"] is False
    assert result.review["source"] == "yaml"
    assert "invalid_packet_id_mismatch" in result.review["errors"]
    assert any(blocker["code"] == "missing_accepted_review" for blocker in result.blockers)


def test_git_mutation_gate_invalid_evidence_blocks_mutation(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path, evidence=False)
    _write_evidence(packet.parent, valid=False)
    (worktree / "allowed" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True)

    assert result.ok is False
    assert any(blocker["code"] == "invalid_evidence_manifest" for blocker in result.blockers)


def test_git_mutation_gate_scope_violation_blocks_mutation(tmp_path: Path) -> None:
    repo, worktree_root, worktree, packet = _fixture(tmp_path)
    (worktree / "frozen" / "change.txt").write_text("change\n", encoding="utf-8")

    result = _run(packet, repo, worktree_root, worktree, dry_run=False, apply=True, commit=True)

    assert result.ok is False
    assert any(blocker["code"] == "scope_guard_failed" for blocker in result.blockers)


def test_git_mutation_gate_main_repo_worktree_path_is_rejected(tmp_path: Path) -> None:
    repo, worktree_root, _worktree, packet = _fixture(tmp_path)

    result = _run(packet, repo, worktree_root, repo, dry_run=False, apply=True, commit=True)

    assert result.ok is False
    assert any(blocker["code"] == "main_repo_worktree_rejected" for blocker in result.blockers)
