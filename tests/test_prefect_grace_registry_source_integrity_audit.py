from __future__ import annotations

from pathlib import Path
import json

import yaml

from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.registry_source_integrity_audit import (
    GitTrackingCheck,
    audit_registry_source_integrity,
)


def _packet_text(packet_id: str) -> str:
    feature_id = packet_id.split("-W", 1)[0]
    return f"""# Execution Packet: {packet_id}

## Objective

Implement a bounded audit test packet.

## Slice

- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-TEST`

## Allowed Write Scope

- prefect_grace/platform/example.py

## Frozen Scope

- backend/**

## Must Preserve

- Runtime registry is read-only.

## Verification

pytest -q tests/test_prefect_grace_registry_source_integrity_audit.py

## Expected Evidence

- pytest output

## Escalation Triggers

- missing source
"""


def _write_project(repo: Path) -> Path:
    project = repo / "prefect_grace" / "project.yaml"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        f"""version: 1
project_key: test-project
repo_root: {repo}
default_branch: test
grace_dir: grace
packets_dir: prefect_grace/packets
runtime_state_root: {repo / "runtime"}
artifact_root: {repo / "runtime" / "artifacts"}
worktree_root: {repo / "runtime" / "worktrees"}
workflow_runtime: prefect
prefect:
  work_pool: test-process
  live_queue: grace-live
  monitoring_queue: grace-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""",
        encoding="utf-8",
    )
    return project


def _write_packet(repo: Path, packet_id: str) -> tuple[Path, str]:
    feature_id = packet_id.split("-W", 1)[0]
    packet_dir = repo / "prefect_grace" / "packets" / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    source = packet_dir / "EXECUTION_PACKET.md"
    source.write_text(_packet_text(packet_id), encoding="utf-8")
    parsed = parse_packet_markdown(source, mode="strict")
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir()
    (reviews / "review-0001.md").write_text("verdict: accepted\n", encoding="utf-8")
    evidence = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence.mkdir(parents=True)
    (evidence / "evidence_manifest.json").write_text(
        json.dumps({"packet_id": packet_id, "generated_by": "pytest", "evidence": [], "blockers": []}),
        encoding="utf-8",
    )
    return source, parsed.source_hash


def _write_registry(repo: Path, *records: dict) -> None:
    state = repo / "runtime" / "state"
    state.mkdir(parents=True)
    payload = {record["packet_id"]: record for record in records}
    (state / "packet_registry.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def _accepted_record(repo: Path, packet_id: str, source: Path, source_hash: str) -> dict:
    return {
        "packet_id": packet_id,
        "path": str(source.relative_to(repo)),
        "registry_status": "accepted",
        "source_hash": source_hash,
    }


def _tracked(_: Path, __: Path) -> GitTrackingCheck:
    return GitTrackingCheck(tracked=True)


def _untracked(_: Path, __: Path) -> GitTrackingCheck:
    return GitTrackingCheck(tracked=False)


def test_accepted_tracked_source_valid_evidence_is_clean(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-CLEAN-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(
        project_config=project,
        git_tracking_checker=_tracked,
    )

    assert result.ok is True
    assert result.issue_counts == {}
    assert result.packets[0]["source_exists"] is True
    assert result.packets[0]["source_tracked_by_git"] is True
    assert result.packets[0]["latest_evidence_manifest_valid"] is True
    assert result.packets[0]["latest_review_status"] == "accepted"


def test_bold_backtick_review_verdict_is_parsed_through_full_audit(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-BOLD-REVIEW-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    (source.parent / "REVIEWS" / "review-0002.md").write_text(
        """# Review 0002

**Verdict:** `accepted`

## Reasons

- accepted after rework
""",
        encoding="utf-8",
    )
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is True
    assert result.packets[0]["latest_review_path"].endswith("REVIEWS/review-0002.md")
    assert result.packets[0]["latest_review_status"] == "accepted"


def test_verdict_section_review_status_is_parsed_through_full_audit(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-SECTION-REVIEW-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    (source.parent / "REVIEWS" / "review-0002.md").write_text(
        """# Review 0002

## Verdict

Accepted.

## Reasons

- accepted after rework
""",
        encoding="utf-8",
    )
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is True
    assert result.packets[0]["latest_review_status"] == "accepted"


def test_yaml_review_status_overrides_markdown_in_full_audit(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-YAML-REVIEW-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    review = source.parent / "REVIEWS" / "review-0002.md"
    review.write_text("verdict: accepted\n", encoding="utf-8")
    review.with_suffix(".yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "artifact_type": "review",
                "packet_id": packet_id,
                "status": "rework_required",
                "generated_by": "pytest",
                "timestamp": "2026-05-28T10:00:00+00:00",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is True
    assert result.packets[0]["latest_review_path"].endswith("REVIEWS/review-0002.yaml")
    assert result.packets[0]["latest_review_status"] == "rework_required"


def test_source_missing_is_blocking(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-MISSING-W01-PACKET"
    _write_registry(
        tmp_path,
        {
            "packet_id": packet_id,
            "path": "prefect_grace/packets/FEAT-MISSING/EXECUTION_PACKET.md",
            "registry_status": "accepted",
            "source_hash": "sha256:missing",
        },
    )

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is False
    assert result.issue_counts["source_missing"] == 1
    assert result.issues[0]["severity"] == "blocking"


def test_source_untracked_is_blocking(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-UNTRACKED-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_untracked)

    assert result.ok is False
    assert result.issue_counts["source_untracked"] == 1
    assert result.packets[0]["source_tracked_by_git"] is False


def test_invalid_evidence_manifest_unknown_packet_id_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-BAD-EVIDENCE-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    manifest = source.parent / "EVIDENCE" / "attempt-0001" / "evidence_manifest.json"
    manifest.write_text(
        json.dumps({"packet_id": "UNKNOWN", "generated_by": "pytest", "evidence": [], "blockers": []}),
        encoding="utf-8",
    )
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is False
    assert result.issue_counts["evidence_manifest_invalid"] == 1
    assert "manifest_packet_id_unknown" in result.issues[0]["message"]


def test_source_hash_mismatch_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-HASH-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    record = _accepted_record(tmp_path, packet_id, source, source_hash)
    record["source_hash"] = "sha256:wrong"
    _write_registry(tmp_path, record)

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is False
    assert result.issue_counts["source_hash_mismatch"] == 1
    assert result.packets[0]["source_hash_matches_current_source"] is False


def test_evidence_dir_without_manifest_is_blocking(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-MISSING-MANIFEST-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    (source.parent / "EVIDENCE" / "attempt-0001" / "evidence_manifest.json").unlink()
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is False
    assert result.issue_counts["evidence_manifest_missing"] == 1
    assert result.issues[0]["severity"] == "blocking"


def test_no_evidence_dir_is_warning_not_blocking(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-NO-EVIDENCE-W01-PACKET"
    source, source_hash = _write_packet(tmp_path, packet_id)
    for path in sorted((source.parent / "EVIDENCE").glob("**/*"), reverse=True):
        if path.is_file():
            path.unlink()
        else:
            path.rmdir()
    (source.parent / "EVIDENCE").rmdir()
    _write_registry(tmp_path, _accepted_record(tmp_path, packet_id, source, source_hash))

    result = audit_registry_source_integrity(project_config=project, git_tracking_checker=_tracked)

    assert result.ok is True
    assert result.issue_counts["evidence_manifest_missing"] == 1
    assert result.issues[0]["severity"] == "warning"
