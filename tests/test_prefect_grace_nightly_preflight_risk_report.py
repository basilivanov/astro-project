"""
Unit tests for nightly preflight risk report.
"""

import json
from pathlib import Path
import pytest
import tempfile
import shutil

from prefect_grace.platform.nightly_preflight_risk_report import (
    generate_nightly_preflight_risk_report,
    PacketRiskFlags,
    _classify_risk_flags,
    _detect_conflicts,
    _estimate_cost,
    _check_review,
    _check_evidence,
    PacketRiskSummary,
)
from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.status_model import RegistryStatus


def _write_review_check_packet(packet_file: Path, packet_id: str = "FEAT-TEST-W01") -> None:
    packet_file.write_text(
        f"""# Execution Packet: {packet_id}

## Objective
Test packet.

## Slice
- packet_id: `{packet_id}`
- feature_id: `FEAT-TEST`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests.

## Verification
pytest

## Expected Evidence
- test output

## Escalation Triggers
- none
""",
        encoding="utf-8",
    )


def _write_review_yaml(packet_dir: Path, *, status: str, packet_id: str = "FEAT-TEST-W01") -> None:
    (packet_dir / "REVIEWS" / "review-0001.yaml").write_text(
        f"""schema_version: 1
artifact_type: review
packet_id: {packet_id}
status: {status}
generated_by: pytest
reviewed_at: 2026-05-28 12:34:56
summary: nightly preflight review sidecar
""",
        encoding="utf-8",
    )


def test_estimate_cost_unit():
    assert _estimate_cost("pytest -q tests/test_foo.py", "unit test") == "targeted"
    assert _estimate_cost("pytest tests/", "run all tests") == "unit"


def test_estimate_cost_docker():
    assert _estimate_cost("docker compose up", "start services") == "docker_required"


def test_estimate_cost_frontend():
    assert _estimate_cost("playwright test", "frontend tests") == "frontend_quick"


def test_estimate_cost_backend():
    assert _estimate_cost("pytest --backend-quick", "backend smoke") == "backend_quick"


def test_estimate_cost_live():
    assert _estimate_cost("run live e2e test", "integration test") == "live_required"


def test_estimate_cost_unknown():
    assert _estimate_cost("", "") == "unknown"


def test_check_review_missing(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Test")

    has_review, accepted = _check_review(packet_file)
    assert not has_review
    assert not accepted


def test_check_review_present_not_accepted(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    review_file = reviews_dir / "review-0001.md"
    review_file.write_text("# Review\n\nStatus: rework_required")

    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert not accepted


def test_check_review_accepted(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    review_file = reviews_dir / "review-0001.md"
    review_file.write_text("# Review\n\nStatus: accepted")

    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert accepted


def test_check_review_yaml_sidecar_overrides_markdown(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("# Review\n\nStatus: accepted", encoding="utf-8")
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)
    _write_review_yaml(packet_dir, status="rework_required")

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert not accepted


def test_check_review_yaml_sidecar_accepts_unquoted_timestamp(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("# Review\n\nStatus: rework_required", encoding="utf-8")
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)
    _write_review_yaml(packet_dir, status="accepted")

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert accepted


def test_check_review_yaml_only_accepted(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)
    _write_review_yaml(packet_dir, status="accepted")

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert accepted


def test_check_review_yaml_only_packet_id_mismatch_fails_closed(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)
    _write_review_yaml(packet_dir, status="accepted", packet_id="FEAT-OTHER-W01")

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert not accepted


def test_check_review_yaml_packet_id_mismatch_fails_closed(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("# Review\n\nStatus: accepted", encoding="utf-8")
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    _write_review_check_packet(packet_file)
    _write_review_yaml(packet_dir, status="accepted", packet_id="FEAT-OTHER-W01")

    has_review, accepted = _check_review(packet_file)
    assert has_review
    assert not accepted


def test_check_evidence_missing(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Test")

    has_evidence, valid = _check_evidence(packet_file)
    assert not has_evidence
    assert not valid


def test_check_evidence_present(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    evidence_dir = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest_file = evidence_dir / "evidence_manifest.json"
    manifest_file.write_text('{"evidence": []}')

    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Test")

    has_evidence, valid = _check_evidence(packet_file)
    assert has_evidence
    assert valid


def test_classify_risk_flags_dependency_blocked(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready
depends_on: FEAT-OTHER-W01

## Objective
Test packet

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)
    parsed = parse_packet_markdown(packet_file, mode="lenient")

    registry_record = {
        "packet_id": "FEAT-TEST-W01",
        "registry_status": RegistryStatus.WAITING_FOR_DEPENDENCIES.value,
    }

    flags = _classify_risk_flags("FEAT-TEST-W01", packet_file, parsed, registry_record, "ready")
    assert flags.dependency_blocked


def test_classify_risk_flags_review_missing(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready

## Objective
Test packet

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)
    parsed = parse_packet_markdown(packet_file, mode="lenient")

    flags = _classify_risk_flags("FEAT-TEST-W01", packet_file, parsed, None, "ready")
    assert flags.review_missing


def test_classify_risk_flags_needs_live_agent(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready

## Objective
Test packet with live execution

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
Run with --execute-agent for live validation

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)
    parsed = parse_packet_markdown(packet_file, mode="lenient")

    flags = _classify_risk_flags("FEAT-TEST-W01", packet_file, parsed, None, "ready")
    assert flags.needs_live_agent
    assert flags.operator_approval_required


def test_classify_risk_flags_needs_git_commit(tmp_path):
    packet_dir = tmp_path / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready

## Objective
Test packet with git mutation

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
Run tests and commit changes

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)
    parsed = parse_packet_markdown(packet_file, mode="lenient")

    flags = _classify_risk_flags("FEAT-TEST-W01", packet_file, parsed, None, "ready")
    assert flags.needs_git_commit


def test_detect_conflicts_no_conflicts():
    summaries = [
        PacketRiskSummary(
            packet_id="FEAT-A-W01",
            registry_status="ready",
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["a.py"],
        ),
        PacketRiskSummary(
            packet_id="FEAT-B-W01",
            registry_status="ready",
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["b.py"],
        ),
    ]

    conflicts = _detect_conflicts(summaries)
    assert len(conflicts) == 0


def test_detect_conflicts_with_conflicts():
    summaries = [
        PacketRiskSummary(
            packet_id="FEAT-A-W01",
            registry_status="ready",
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["shared.py", "a.py"],
        ),
        PacketRiskSummary(
            packet_id="FEAT-B-W01",
            registry_status="ready",
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["shared.py", "b.py"],
        ),
    ]

    conflicts = _detect_conflicts(summaries)
    assert len(conflicts) == 1
    assert set(conflicts[0].packet_ids) == {"FEAT-A-W01", "FEAT-B-W01"}
    assert "shared.py" in conflicts[0].conflicting_paths


def test_generate_nightly_preflight_risk_report_project_load_failed():
    result = generate_nightly_preflight_risk_report(project_config="/nonexistent/path")
    assert not result.ok
    assert len(result.errors) > 0
    assert result.errors[0]["code"] == "PROJECT_LOAD_FAILED"


def test_generate_nightly_preflight_risk_report_bounded_output(tmp_path):
    """Test that output is bounded with totals."""
    # Create a minimal project structure
    project_root = tmp_path / "project"
    project_root.mkdir()

    packets_dir = project_root / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    state_dir = project_root / "state"
    state_dir.mkdir()

    # Create project config
    project_yaml = project_root / "prefect_grace" / "project.yaml"
    project_yaml.parent.mkdir(exist_ok=True)
    project_yaml.write_text("""
project_key: test-project
repo_root: .
packets_dir: prefect_grace/packets
runtime_state_root: state
""")

    # Create a valid packet
    packet_dir = packets_dir / "FEAT-TEST-W01"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: FEAT-TEST-W01

status: ready
feature_id: FEAT-TEST
wave_id: W01

## Objective
Test packet

## Allowed Write Scope
- test.py

## Frozen Scope
- frozen.py

## Must Preserve
- Keep tests

## Verification
pytest -q

## Expected Evidence
- test output

## Escalation Triggers
- none
"""
    packet_file.write_text(packet_content)

    # Create registry
    registry_file = state_dir / "packet_registry.yaml"
    registry_file.write_text("""packets:
  FEAT-TEST-W01:
    packet_id: FEAT-TEST-W01
    registry_status: ready
    source_hash: sha256:abc123
""")

    result = generate_nightly_preflight_risk_report(project_config=project_yaml)

    # Check bounded output
    result_dict = result.to_dict()
    assert "safe_candidates_total" in result_dict
    assert "risky_candidates_total" in result_dict
    assert "blocked_candidates_total" in result_dict
    assert "approval_required_candidates_total" in result_dict
    assert "conflict_groups_total" in result_dict
    assert len(result_dict["safe_candidates"]) <= 25
    assert len(result_dict["packet_summaries"]) <= 25
