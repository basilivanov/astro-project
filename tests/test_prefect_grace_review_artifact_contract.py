from pathlib import Path

from prefect_grace.platform.review_artifact_contract import (
    read_review_artifact_status,
    read_review_status,
)


def test_valid_yaml_review_artifact_is_accepted(tmp_path: Path) -> None:
    review = tmp_path / "review-0001.yaml"
    review.write_text(
        """schema_version: 1
artifact_type: review
packet_id: FEAT-TEST-W01-PACKET
status: accepted
reviewer: qa
reviewed_at: "2026-05-28T10:00:00+00:00"
""",
        encoding="utf-8",
    )

    result = read_review_artifact_status(
        review,
        expected_packet_id="FEAT-TEST-W01-PACKET",
    )

    assert result.ok is True
    assert result.status == "accepted"
    assert result.source == "yaml"


def test_unquoted_yaml_timestamp_is_normalized_to_string(tmp_path: Path) -> None:
    review = tmp_path / "review-0001.yaml"
    review.write_text(
        """schema_version: 1
artifact_type: review
packet_id: FEAT-TEST-W01-PACKET
status: accepted
generated_by: pytest
timestamp: 2026-05-28T10:00:00+00:00
""",
        encoding="utf-8",
    )

    result = read_review_artifact_status(
        review,
        expected_packet_id="FEAT-TEST-W01-PACKET",
    )

    assert result.ok is True
    assert result.status == "accepted"
    assert result.artifact is not None
    assert result.artifact.reviewed_at == "2026-05-28T10:00:00+00:00"
    assert isinstance(result.artifact.reviewed_at, str)
    assert isinstance(result.artifact.raw["timestamp"], str)


def test_yaml_review_artifact_rejects_missing_or_invalid_verdict(tmp_path: Path) -> None:
    review = tmp_path / "review-0001.yaml"
    review.write_text(
        """schema_version: 1
artifact_type: review
packet_id: FEAT-TEST-W01-PACKET
reviewer: qa
reviewed_at: "2026-05-28T10:00:00+00:00"
""",
        encoding="utf-8",
    )

    result = read_review_artifact_status(review)

    assert result.ok is False
    assert result.status is None
    assert "missing_or_invalid_verdict" in result.errors
    assert read_review_status(review) == "invalid"


def test_yaml_review_artifact_rejects_packet_id_mismatch(tmp_path: Path) -> None:
    review = tmp_path / "review-0001.yaml"
    review.write_text(
        """schema_version: 1
artifact_type: review
packet_id: FEAT-OTHER-W01-PACKET
status: accepted
generated_by: pytest
timestamp: "2026-05-28T10:00:00+00:00"
""",
        encoding="utf-8",
    )

    result = read_review_artifact_status(
        review,
        expected_packet_id="FEAT-TEST-W01-PACKET",
    )

    assert result.ok is False
    assert "invalid_packet_id_mismatch" in result.errors


def test_yaml_sidecar_overrides_misleading_markdown_fallback(tmp_path: Path) -> None:
    review = tmp_path / "review-0001.md"
    review.write_text("verdict: accepted\n", encoding="utf-8")
    review.with_suffix(".yaml").write_text(
        """schema_version: 1
artifact_type: review
status: rework_required
generated_by: verifier
timestamp: "2026-05-28T10:00:00+00:00"
""",
        encoding="utf-8",
    )

    result = read_review_artifact_status(review)

    assert result.ok is True
    assert result.status == "rework_required"
    assert result.path == review.with_suffix(".yaml")
    assert result.source == "yaml"


def test_legacy_markdown_review_fallback_still_parses_old_reviews(tmp_path: Path) -> None:
    review = tmp_path / "review-0001.md"
    review.write_text(
        """# Review

**Verdict:** ✅ ACCEPTED
""",
        encoding="utf-8",
    )

    result = read_review_artifact_status(review)

    assert result.ok is True
    assert result.status == "accepted"
    assert result.source == "markdown"
