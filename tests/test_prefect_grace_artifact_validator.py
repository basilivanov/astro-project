"""Tests for prefect_grace.platform.artifact_validator module."""

import pytest
import tempfile
from pathlib import Path
from prefect_grace.platform.artifact_validator import (
    ArtifactReference,
    ArtifactValidationResult,
    validate_artifact_references,
)
from prefect_grace.platform.evidence_manifest import (
    EvidenceItem,
    EvidenceManifest,
)


def test_artifact_reference_to_dict():
    """Test ArtifactReference serialization."""
    ref = ArtifactReference(
        path="test-output.txt",
        exists=True,
        size=1024,
        hash="abc123",
    )

    data = ref.to_dict()

    assert data["path"] == "test-output.txt"
    assert data["exists"] is True
    assert data["size"] == 1024
    assert data["hash"] == "abc123"


def test_artifact_validation_result_to_dict():
    """Test ArtifactValidationResult serialization."""
    ref = ArtifactReference(
        path="test-output.txt",
        exists=True,
        size=1024,
        hash="abc123",
    )

    result = ArtifactValidationResult(
        ok=True,
        validated_artifacts=[ref],
        missing_artifacts=[],
    )

    data = result.to_dict()

    assert data["ok"] is True
    assert len(data["validated_artifacts"]) == 1
    assert data["validated_artifacts"][0]["path"] == "test-output.txt"
    assert data["missing_artifacts"] == []


def test_validate_artifact_references_all_exist():
    """Test validation when all artifacts exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test artifact
        artifact_path = tmpdir_path / "test-output.txt"
        artifact_path.write_text("test output")

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[str(artifact_path)],
            summary="All tests passed",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [tmpdir_path])

        assert result.ok is True
        assert len(result.validated_artifacts) == 1
        assert result.validated_artifacts[0].exists is True
        assert result.validated_artifacts[0].size > 0
        assert result.validated_artifacts[0].hash is not None
        assert len(result.missing_artifacts) == 0


def test_validate_artifact_references_missing():
    """Test validation catches missing artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Reference non-existent artifact
        artifact_path = tmpdir_path / "nonexistent.txt"

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[str(artifact_path)],
            summary="All tests passed",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [tmpdir_path])

        assert result.ok is False
        assert len(result.validated_artifacts) == 1
        assert result.validated_artifacts[0].exists is False
        assert result.validated_artifacts[0].size is None
        assert result.validated_artifacts[0].hash is None
        assert len(result.missing_artifacts) == 1
        assert str(artifact_path) in result.missing_artifacts


def test_validate_artifact_references_outside_root():
    """Test validation catches paths outside artifact roots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create artifact outside allowed root
        outside_dir = Path(tempfile.mkdtemp())
        artifact_path = outside_dir / "test-output.txt"
        artifact_path.write_text("test output")

        try:
            item = EvidenceItem(
                id="EV-TEST-001",
                status="collected",
                stage="packet_local",
                producer="pytest",
                artifact_paths=[str(artifact_path)],
                summary="All tests passed",
            )

            manifest = EvidenceManifest(
                packet_id="PKT-001",
                generated_by="verifier",
                evidence=[item],
                blockers=[],
            )

            result = validate_artifact_references(manifest, [tmpdir_path])

            # Artifact exists but is outside allowed root
            assert result.ok is False
            assert len(result.validated_artifacts) == 1
            assert result.validated_artifacts[0].exists is False
            assert len(result.missing_artifacts) == 1
        finally:
            artifact_path.unlink()
            outside_dir.rmdir()


def test_validate_artifact_references_relative_path():
    """Test validation handles relative paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test artifact
        artifact_path = tmpdir_path / "test-output.txt"
        artifact_path.write_text("test output")

        # Use relative path
        relative_path = "test-output.txt"

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[relative_path],
            summary="All tests passed",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        # Relative paths are resolved against artifact_roots
        result = validate_artifact_references(manifest, [tmpdir_path])

        # Relative path found in artifact_root
        assert result.ok is True
        assert len(result.validated_artifacts) == 1
        assert result.validated_artifacts[0].exists is True
        assert result.validated_artifacts[0].size == 11
        assert result.validated_artifacts[0].hash is not None


def test_validate_artifact_references_rejects_relative_traversal_outside_root():
    """Test validation rejects relative paths that escape the allowed root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        root = tmpdir_path / "root"
        root.mkdir()
        outside = tmpdir_path / "outside.txt"
        outside.write_text("outside")

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=["../outside.txt"],
            summary="Traversal attempt",
        )
        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [root])

        assert result.ok is False
        assert len(result.validated_artifacts) == 1
        assert result.validated_artifacts[0].path == "../outside.txt"
        assert result.validated_artifacts[0].exists is False
        assert result.missing_artifacts == ["../outside.txt"]


def test_validate_artifact_references_records_metadata():
    """Test validation records size and hash metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test artifact with known content
        artifact_path = tmpdir_path / "test-output.txt"
        test_content = "test output content"
        artifact_path.write_text(test_content)

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[str(artifact_path)],
            summary="All tests passed",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [tmpdir_path])

        assert result.ok is True
        assert len(result.validated_artifacts) == 1
        ref = result.validated_artifacts[0]
        assert ref.exists is True
        assert ref.size == len(test_content)
        assert ref.hash is not None
        assert len(ref.hash) == 64  # SHA-256 hex digest length


def test_validate_artifact_references_skips_non_collected():
    """Test validation skips evidence items with status != collected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        item1 = EvidenceItem(
            id="EV-TEST-001",
            status="missing",  # Not collected
            stage="packet_local",
            producer="pytest",
            artifact_paths=["nonexistent.txt"],
            summary="Tests not run",
        )

        item2 = EvidenceItem(
            id="EV-TEST-002",
            status="deferred",  # Not collected
            stage="wave_final",
            producer="log_watch",
            artifact_paths=["logs.txt"],
            summary="Deferred to wave-final",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item1, item2],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [tmpdir_path])

        # No artifacts validated because none have status=collected
        assert result.ok is True
        assert len(result.validated_artifacts) == 0
        assert len(result.missing_artifacts) == 0


def test_validate_artifact_references_multiple_artifacts():
    """Test validation handles multiple artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create multiple test artifacts
        artifact1 = tmpdir_path / "test-output-1.txt"
        artifact1.write_text("test 1")

        artifact2 = tmpdir_path / "test-output-2.txt"
        artifact2.write_text("test 2")

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[str(artifact1), str(artifact2)],
            summary="All tests passed",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [tmpdir_path])

        assert result.ok is True
        assert len(result.validated_artifacts) == 2
        assert all(ref.exists for ref in result.validated_artifacts)
        assert len(result.missing_artifacts) == 0


def test_validate_artifact_references_mixed_exists_missing():
    """Test validation handles mix of existing and missing artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create one artifact, reference another that doesn't exist
        artifact1 = tmpdir_path / "exists.txt"
        artifact1.write_text("exists")

        artifact2 = tmpdir_path / "missing.txt"

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[str(artifact1), str(artifact2)],
            summary="Partial results",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        result = validate_artifact_references(manifest, [tmpdir_path])

        assert result.ok is False
        assert len(result.validated_artifacts) == 2
        assert result.validated_artifacts[0].exists is True
        assert result.validated_artifacts[1].exists is False
        assert len(result.missing_artifacts) == 1
        assert str(artifact2) in result.missing_artifacts


def test_validate_artifact_references_empty_manifest():
    """Test validation handles empty manifest."""
    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[],
        blockers=[],
    )

    result = validate_artifact_references(manifest, [])

    assert result.ok is True
    assert len(result.validated_artifacts) == 0
    assert len(result.missing_artifacts) == 0


def test_validate_artifact_references_no_artifact_roots():
    """Test validation with no artifact roots specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test artifact
        artifact_path = tmpdir_path / "test-output.txt"
        artifact_path.write_text("test output")

        item = EvidenceItem(
            id="EV-TEST-001",
            status="collected",
            stage="packet_local",
            producer="pytest",
            artifact_paths=[str(artifact_path)],
            summary="All tests passed",
        )

        manifest = EvidenceManifest(
            packet_id="PKT-001",
            generated_by="verifier",
            evidence=[item],
            blockers=[],
        )

        # No artifact roots - absolute paths still validated
        result = validate_artifact_references(manifest, [])

        assert result.ok is True
        assert len(result.validated_artifacts) == 1
        assert result.validated_artifacts[0].exists is True
