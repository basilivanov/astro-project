import json
import subprocess
from pathlib import Path

from prefect_grace.platform.git_sync import run_git_sync
from prefect_grace.platform.git_mutation_gate import run_git_mutation_gate


PACKET_ID = "FEAT-GRACE-ORCHESTRATOR-GIT-SYNC-W01-AUTO-BRANCHING"
PROJECT_KEY = "astro-project"
BRANCH = f"agent/{PROJECT_KEY}/{PACKET_ID}/attempt-0001"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def _write_packet(packet: Path) -> None:
    packet.write_text(
        f"""# Execution Packet: {PACKET_ID}

## Objective
Temp git sync packet.

## Slice
- packet_id: `{PACKET_ID}`
- feature_id: `FEAT-GRACE-ORCHESTRATOR-GIT-SYNC`
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
- EVIDENCE/attempt-0001/evidence_manifest.json

## Escalation Triggers
- Git mutations fail.
""",
        encoding="utf-8",
    )
    # Also write sidecar YAML
    sidecar = packet.with_suffix(".yaml")
    sidecar.write_text(
        f"""schema_version: "1"
artifact_type: execution_packet
packet_id: {PACKET_ID}
feature_id: FEAT-GRACE-ORCHESTRATOR-GIT-SYNC
wave_id: W01
title: {PACKET_ID}
objective: Temp objective
status: ready
phase: PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP
depends_on: []
modules:
- M-GRACE-GIT-SYNC
allowed_write_scope:
- allowed/**
frozen_scope:
- frozen/**
must_preserve:
- Git mutations stay guarded.
verification: |
  pytest
expected_evidence:
- EVIDENCE/attempt-0001/evidence_manifest.json
escalation_triggers:
- Git mutations fail.
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


def _fixture(tmp_path: Path, *, review: bool = True, evidence: bool = True) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    worktree_root = tmp_path / "worktrees"
    repo.mkdir()
    worktree_root.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")
    packet_dir = repo / "packets" / "FEAT-GRACE-ORCHESTRATOR-GIT-SYNC"
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
    return repo, worktree_root, packet


def test_git_sync_creates_branch_and_worktree(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path)
    result = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        dry_run=True,
    )
    assert result.ok is True
    assert result.status == "planned"
    assert result.branch_name == BRANCH
    assert Path(result.worktree_path).exists()


def test_git_sync_resolves_existing_worktree(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path)
    # Run once to create worktree
    result1 = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        dry_run=True,
    )
    # Run again to ensure it resolves the existing worktree
    result2 = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        dry_run=True,
    )
    assert result2.ok is True
    assert result2.worktree_path == result1.worktree_path
    assert result2.branch_name == result1.branch_name


def test_git_sync_blocked_when_review_missing(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path, review=False)
    result = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        dry_run=True,
    )
    assert result.ok is False
    assert result.review_status == "missing"
    assert "missing_accepted_review" in result.blocker_reason


def test_git_sync_blocked_when_review_not_accepted(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path, review=True)
    _write_review(packet.parent, accepted=False)
    result = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        dry_run=True,
    )
    assert result.ok is False
    assert result.review_status == "not_accepted"
    assert "missing_accepted_review" in result.blocker_reason


def test_git_sync_applies_mutation_gate(tmp_path: Path) -> None:
    repo, worktree_root, packet = _fixture(tmp_path)
    
    # Run once to create worktree
    res_dry = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        dry_run=True,
    )
    wt_path = Path(res_dry.worktree_path)
    
    # Make a change in the isolated worktree
    (wt_path / "allowed" / "change.txt").write_text("valid change", encoding="utf-8")
    
    # Setup a mock remote bare repository so git push actually succeeds
    remote_repo = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "remote.git")
    _git(repo, "remote", "add", "origin", str(remote_repo))
    _git(wt_path, "remote", "set-url", "origin", str(remote_repo))
    
    result = run_git_sync(
        packet=packet,
        repo_root=repo,
        worktree_root=worktree_root,
        project_key=PROJECT_KEY,
        packet_id=PACKET_ID,
        attempt=1,
        base_ref="main",
        remote="origin",
        dry_run=False,
        apply=True,
    )
    
    assert result.ok is True
    assert result.status == "applied"
    assert result.commit_sha is not None
    assert result.pushed_ref is not None
