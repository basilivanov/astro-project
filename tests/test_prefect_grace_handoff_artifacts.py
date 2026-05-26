"""Tests for handoff artifact helpers."""

from pathlib import Path
import pytest
from prefect_grace.tasks.handoff_artifacts import (
    write_handoff_summary,
    format_evidence_summary,
    format_review_summary,
)


def test_write_handoff_summary(tmp_path):
    """Test writing handoff summary."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    handoff_result = {
        "packet_id": "TEST-001",
        "attempt": 1,
        "domain_status": "accepted",
        "verifier": {
            "ok": True,
            "marker_found": True,
            "errors": [],
        },
        "reviewer": {
            "ok": True,
            "marker_found": True,
            "errors": [],
        },
        "evidence_manifest_path": "EVIDENCE/attempt-0001/evidence_manifest.json",
        "review_path": "REVIEWS/review-0001.md",
        "rework_path": None,
    }

    summary_path = write_handoff_summary(packet_dir, handoff_result)

    assert summary_path.exists()
    assert summary_path.name == "SUMMARY.md"

    content = summary_path.read_text(encoding="utf-8")
    assert "TEST-001" in content
    assert "accepted" in content
    assert "Verifier Result" in content
    assert "Reviewer Result" in content


def test_write_handoff_summary_verifier_failed(tmp_path):
    """Test writing handoff summary when verifier failed."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    handoff_result = {
        "packet_id": "TEST-001",
        "attempt": 1,
        "domain_status": "verifier_failed",
        "verifier": {
            "ok": False,
            "marker_found": False,
            "errors": ["Marker not found"],
        },
        "reviewer": None,
        "evidence_manifest_path": None,
        "review_path": None,
        "rework_path": None,
    }

    summary_path = write_handoff_summary(packet_dir, handoff_result)

    assert summary_path.exists()

    content = summary_path.read_text(encoding="utf-8")
    assert "verifier_failed" in content
    assert "Not executed (verifier failed)" in content


def test_format_evidence_summary_valid():
    """Test formatting evidence summary."""
    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["artifacts/test.txt"],
                "summary": "Tests passed"
            },
            {
                "id": "EV-TEST-002",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["artifacts/test2.txt"],
                "summary": "More tests passed"
            }
        ]
    }

    summary = format_evidence_summary(evidence_json)

    assert "Evidence Summary" in summary
    assert "**Total Requirements:** 2" in summary
    assert "collected: 2" in summary


def test_format_evidence_summary_mixed_statuses():
    """Test formatting evidence summary with mixed statuses."""
    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["artifacts/test.txt"],
                "summary": "Tests passed"
            },
            {
                "id": "EV-TEST-002",
                "status": "missing",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": [],
                "summary": "Tests not run"
            },
            {
                "id": "EV-TEST-003",
                "status": "deferred",
                "stage": "wave_final",
                "producer": "pytest",
                "artifact_paths": [],
                "summary": "Deferred to wave final"
            }
        ]
    }

    summary = format_evidence_summary(evidence_json)

    assert "**Total Requirements:** 3" in summary
    assert "collected: 1" in summary
    assert "missing: 1" in summary
    assert "deferred: 1" in summary


def test_format_evidence_summary_none():
    """Test formatting evidence summary when None."""
    summary = format_evidence_summary(None)

    assert summary == "No evidence manifest"


def test_format_review_summary_accepted():
    """Test formatting review summary for accepted verdict."""
    decision_json = {
        "packet_verdict": "accepted",
        "route_classification": None,
        "rework_mode": None,
        "reasons": []
    }

    summary = format_review_summary(decision_json)

    assert "Review Summary" in summary
    assert "**Verdict:** accepted" in summary


def test_format_review_summary_rework_required():
    """Test formatting review summary for rework_required verdict."""
    decision_json = {
        "packet_verdict": "rework_required",
        "route_classification": "self_resolvable_rework",
        "rework_mode": "bounded_fresh",
        "reasons": ["Missing test coverage", "Incomplete implementation"]
    }

    summary = format_review_summary(decision_json)

    assert "Review Summary" in summary
    assert "**Verdict:** rework_required" in summary
    assert "**Route Classification:** self_resolvable_rework" in summary
    assert "**Rework Mode:** bounded_fresh" in summary
    assert "Missing test coverage" in summary
    assert "Incomplete implementation" in summary


def test_format_review_summary_none():
    """Test formatting review summary when None."""
    summary = format_review_summary(None)

    assert summary == "No reviewer decision"
