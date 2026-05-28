import json
import os
import subprocess
from pathlib import Path

from prefect_grace.platform.merge_steward import run_merge_steward


PACKET_ID_1 = "FEAT-MERGE-TEST-W01-PACKET-A"
PACKET_ID_2 = "FEAT-MERGE-TEST-W01-PACKET-B"
PROJECT_KEY = "astro-project"
BRANCH_1 = f"agent/{PROJECT_KEY}/{PACKET_ID_1}/attempt-0001"
BRANCH_2 = f"agent/{PROJECT_KEY}/{PACKET_ID_2}/attempt-0001"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def _write_packet(packet: Path, packet_id: str) -> None:
    packet.write_text(
        f"""# Execution Packet: {packet_id}

## Objective
Test merge steward packet.

## Slice
- packet_id: `{packet_id}`
- feature_id: `FEAT-MERGE-TEST`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- allowed/**

## Frozen Scope
- frozen/**

## Must Preserve
- Merge steward stays guarded.

## Verification
pytest

## Expected Evidence
- evidence manifest

## Escalation Triggers
- unsafe merge
""",
        encoding="utf-8",
    )


def _write_review(packet_dir: Path, accepted: bool = True) -> None:
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir(parents=True, exist_ok=True)
    status = "accepted" if accepted else "rework_required"
    (reviews / "review-0001.md").write_text(f"status: {status}\n\n## Verdict\n{status}\n", encoding="utf-8")


def _write_review_yaml(packet_dir: Path, *, status: str, packet_id: str) -> None:
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / "review-0001.yaml").write_text(
        f"""schema_version: 1
artifact_type: review
packet_id: {packet_id}
status: {status}
generated_by: pytest
reviewed_at: 2026-05-28 12:34:56
summary: merge steward yaml-only review
""",
        encoding="utf-8",
    )


def _write_evidence(packet_dir: Path, packet_id: str, valid: bool = True) -> None:
    evidence_dir = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    if valid:
        (evidence_dir / "targeted_pytest.txt").write_text("1 passed\n", encoding="utf-8")
    artifact = "targeted_pytest.txt" if valid else "missing.txt"
    (evidence_dir / "evidence_manifest.json").write_text(
        json.dumps(
            {
                "packet_id": packet_id,
                "generated_by": "pytest",
                "evidence": [
                    {
                        "id": "EV-MERGE-001",
                        "status": "collected",
                        "stage": "packet_local",
                        "producer": "pytest",
                        "artifact_paths": [artifact],
                        "summary": "merge steward proof",
                    }
                ],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )


def _setup_repo(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    """Setup test repo with two packet branches."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test User")

    # Create initial commit on main
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "Initial commit")

    # Create packet 1
    packet_dir_1 = repo / "packets" / "FEAT-MERGE-TEST-A"
    packet_dir_1.mkdir(parents=True)
    packet_1 = packet_dir_1 / "EXECUTION_PACKET.md"
    _write_packet(packet_1, PACKET_ID_1)
    _write_review(packet_dir_1, accepted=True)
    _write_evidence(packet_dir_1, PACKET_ID_1, valid=True)

    # Create packet 2
    packet_dir_2 = repo / "packets" / "FEAT-MERGE-TEST-B"
    packet_dir_2.mkdir(parents=True)
    packet_2 = packet_dir_2 / "EXECUTION_PACKET.md"
    _write_packet(packet_2, PACKET_ID_2)
    _write_review(packet_dir_2, accepted=True)
    _write_evidence(packet_dir_2, PACKET_ID_2, valid=True)

    _git(repo, "add", "packets")
    _git(repo, "commit", "-m", "Add packets")

    # Create branch 1 with changes
    _git(repo, "checkout", "-b", BRANCH_1)
    (repo / "file1.txt").write_text("change 1\n", encoding="utf-8")
    _git(repo, "add", "file1.txt")
    _git(repo, "commit", "-m", "Packet 1 changes")

    # Create branch 2 with changes
    _git(repo, "checkout", "main")
    _git(repo, "checkout", "-b", BRANCH_2)
    (repo / "file2.txt").write_text("change 2\n", encoding="utf-8")
    _git(repo, "add", "file2.txt")
    _git(repo, "commit", "-m", "Packet 2 changes")

    # Return to main
    _git(repo, "checkout", "main")

    packet_paths = {
        BRANCH_1: packet_1,
        BRANCH_2: packet_2,
    }

    return repo, packet_paths


def test_merge_steward_dry_run_plan() -> None:
    """Test dry-run produces merge plan without mutation."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1, BRANCH_2],
            packet_paths=packet_paths,
            dry_run=True,
        )

        assert result.ok is True
        assert result.status == "planned"
        assert result.dry_run is True
        assert result.plan is not None
        assert result.plan.target_branch == "main"
        assert result.plan.candidates_total == 2
        assert result.plan.excluded_total == 0
        assert result.plan.fast_forward_eligible is True
        assert result.plan.all_candidates_accepted is True
        assert result.merged_count == 0


def test_merge_steward_accepts_review_from_yaml_sidecar() -> None:
    """YAML sidecar is canonical for accepted-review checks."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)
        review = repo / "packets" / "FEAT-MERGE-TEST-A" / "REVIEWS" / "review-0001.md"
        review.write_text("status: rework_required\n", encoding="utf-8")
        review.with_suffix(".yaml").write_text(
            f"""schema_version: 1
artifact_type: review
packet_id: {PACKET_ID_1}
status: accepted
generated_by: pytest
timestamp: "2026-05-28T10:00:00+00:00"
""",
            encoding="utf-8",
        )

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=True,
        )

        assert result.ok is True
        assert result.plan is not None
        assert result.plan.candidates_total == 1
        assert result.plan.excluded_total == 0


def test_merge_steward_accepts_yaml_only_review() -> None:
    """YAML-only accepted reviews are first-class review artifacts."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)
        packet_dir = repo / "packets" / "FEAT-MERGE-TEST-A"
        for review in (packet_dir / "REVIEWS").glob("review-*.md"):
            review.unlink()
        _write_review_yaml(packet_dir, status="accepted", packet_id=PACKET_ID_1)

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=True,
        )

        assert result.ok is True
        assert result.plan is not None
        assert result.plan.candidates_total == 1
        assert result.plan.excluded_total == 0


def test_merge_steward_missing_approval_blocks() -> None:
    """Test missing approval flags block merge."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=False,
            apply=True,
            merge=True,
            understand_merge=False,  # Missing approval
        )

        assert result.ok is False
        assert result.status == "blocked"
        assert result.blocker_reason == "merge_requires_cli_approval"
        assert any(b["code"] == "merge_requires_cli_approval" for b in result.blockers)


def test_merge_steward_fast_forward_apply() -> None:
    """Test fast-forward merge apply with full approval."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        # Record initial SHA
        initial_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=False,
            apply=True,
            merge=True,
            understand_merge=True,
            merge_approved_env="1",
        )

        assert result.ok is True
        assert result.status == "applied"
        assert result.merged_count == 1
        assert BRANCH_1 in result.merged_sample
        assert result.target_branch_before_sha == initial_sha
        assert result.target_branch_after_sha != initial_sha

        # Verify file exists
        assert (repo / "file1.txt").exists()


def test_merge_steward_non_fast_forward_blocks() -> None:
    """Test non-fast-forward merge is blocked."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        # Make a commit on main that conflicts with branch
        _git(repo, "checkout", "main")
        (repo / "conflict.txt").write_text("main change\n", encoding="utf-8")
        _git(repo, "add", "conflict.txt")
        _git(repo, "commit", "-m", "Main diverged")

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=True,
        )

        assert result.ok is False
        assert result.status == "blocked"
        assert result.plan is not None
        assert result.plan.candidates_total == 0
        assert result.plan.excluded_total == 1
        assert result.plan.excluded_sample[0]["reason"] == "not_fast_forward"


def test_merge_steward_dirty_target_blocks() -> None:
    """Test dirty target repository blocks merge."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        # Make target dirty
        (repo / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=False,
            apply=True,
            merge=True,
            understand_merge=True,
            merge_approved_env="1",
        )

        assert result.ok is False
        assert result.status == "blocked"
        assert result.blocker_reason == "dirty_target_branch"


def test_merge_steward_missing_review_blocks() -> None:
    """Test missing accepted review blocks merge."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        # Remove review
        packet_dir = repo / "packets" / "FEAT-MERGE-TEST-A"
        reviews_dir = packet_dir / "REVIEWS"
        for review in reviews_dir.glob("*.md"):
            review.unlink()

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=True,
        )

        assert result.ok is False
        assert result.status == "blocked"
        assert result.plan is not None
        assert result.plan.candidates_total == 0
        assert result.plan.excluded_total == 1
        assert result.plan.excluded_sample[0]["reason"] == "missing_accepted_review"


def test_merge_steward_invalid_evidence_blocks() -> None:
    """Test invalid evidence blocks merge."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        # Make evidence invalid by removing artifact
        packet_dir = repo / "packets" / "FEAT-MERGE-TEST-A"
        evidence_dir = packet_dir / "EVIDENCE" / "attempt-0001"
        (evidence_dir / "targeted_pytest.txt").unlink()

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=True,
        )

        assert result.ok is False
        assert result.status == "blocked"
        assert result.plan is not None
        assert result.plan.candidates_total == 0
        assert result.plan.excluded_total == 1
        assert result.plan.excluded_sample[0]["reason"] == "invalid_evidence"


def test_merge_steward_no_candidates() -> None:
    """Test no candidates produces warning."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        result = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[],
            packet_paths={},
            dry_run=True,
        )

        assert result.ok is True
        assert result.status == "planned"
        assert len(result.warnings) == 1
        assert result.warnings[0]["code"] == "no_candidates"


def test_merge_steward_env_approval_token() -> None:
    """Test environment approval token is checked."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo, packet_paths = _setup_repo(tmp_path)

        # Set environment variable
        old_env = os.environ.get("GRACE_MERGE_STEWARD_APPROVED")
        try:
            os.environ["GRACE_MERGE_STEWARD_APPROVED"] = "1"

            result = run_merge_steward(
                repo_root=repo,
                target_branch="main",
                packet_branches=[BRANCH_1],
                packet_paths=packet_paths,
                dry_run=False,
                apply=True,
                merge=True,
                understand_merge=True,
            )

            assert result.ok is True
            assert result.status == "applied"
        finally:
            if old_env is None:
                os.environ.pop("GRACE_MERGE_STEWARD_APPROVED", None)
            else:
                os.environ["GRACE_MERGE_STEWARD_APPROVED"] = old_env


def test_merge_steward_multiple_branches() -> None:
    """Test merging multiple branches sequentially."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo = tmp_path / "repo"
        repo.mkdir()
        _git(repo, "init", "-b", "main")
        _git(repo, "config", "user.email", "test@example.invalid")
        _git(repo, "config", "user.name", "Test User")

        # Create initial commit on main
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        _git(repo, "add", "README.md")
        _git(repo, "commit", "-m", "Initial commit")

        # Create packets
        packet_dir_1 = repo / "packets" / "FEAT-MERGE-TEST-A"
        packet_dir_1.mkdir(parents=True)
        packet_1 = packet_dir_1 / "EXECUTION_PACKET.md"
        _write_packet(packet_1, PACKET_ID_1)
        _write_review(packet_dir_1, accepted=True)
        _write_evidence(packet_dir_1, PACKET_ID_1, valid=True)

        packet_dir_2 = repo / "packets" / "FEAT-MERGE-TEST-B"
        packet_dir_2.mkdir(parents=True)
        packet_2 = packet_dir_2 / "EXECUTION_PACKET.md"
        _write_packet(packet_2, PACKET_ID_2)
        _write_review(packet_dir_2, accepted=True)
        _write_evidence(packet_dir_2, PACKET_ID_2, valid=True)

        _git(repo, "add", "packets")
        _git(repo, "commit", "-m", "Add packets")

        # Create branch 1 with changes
        _git(repo, "checkout", "-b", BRANCH_1)
        (repo / "file1.txt").write_text("change 1\n", encoding="utf-8")
        _git(repo, "add", "file1.txt")
        _git(repo, "commit", "-m", "Packet 1 changes")

        # Create branch 2 on top of branch 1 (linear history)
        _git(repo, "checkout", "-b", BRANCH_2)
        (repo / "file2.txt").write_text("change 2\n", encoding="utf-8")
        _git(repo, "add", "file2.txt")
        _git(repo, "commit", "-m", "Packet 2 changes")

        # Return to main
        _git(repo, "checkout", "main")

        packet_paths = {
            BRANCH_1: packet_1,
            BRANCH_2: packet_2,
        }

        # Merge branch 1 first
        result1 = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_1],
            packet_paths=packet_paths,
            dry_run=False,
            apply=True,
            merge=True,
            understand_merge=True,
            merge_approved_env="1",
        )

        assert result1.ok is True
        assert result1.status == "applied"
        assert result1.merged_count == 1
        assert (repo / "file1.txt").exists()

        # Now merge branch 2 (which is on top of branch 1)
        result2 = run_merge_steward(
            repo_root=repo,
            target_branch="main",
            packet_branches=[BRANCH_2],
            packet_paths=packet_paths,
            dry_run=False,
            apply=True,
            merge=True,
            understand_merge=True,
            merge_approved_env="1",
        )

        assert result2.ok is True
        assert result2.status == "applied"
        assert result2.merged_count == 1
        assert (repo / "file2.txt").exists()
